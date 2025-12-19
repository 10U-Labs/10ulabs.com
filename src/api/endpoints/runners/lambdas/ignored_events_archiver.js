const { getCloudWatchClient } = require('/opt/nodejs/runners-layer');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

let s3Client = null;
function getS3Client() {
  if (!s3Client) {
    s3Client = new S3Client({});
  }
  return s3Client;
}
const { PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

async function publishMetric(metricName, value, unit = 'None') {
  try {
    await getCloudWatchClient().send(new PutMetricDataCommand({
      Namespace: 'IgnoredEventsArchiver',
      MetricData: [{
        MetricName: metricName,
        Value: value,
        Unit: unit,
        Timestamp: new Date()
      }]
    }));
  } catch (err) {
    logger.warn('Failed to publish metric', metricName, ':', err.message);
  }
}

function buildS3Key(timestamp, messageId) {
  const date = new Date(timestamp);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hour = String(date.getUTCHours()).padStart(2, '0');

  return `ignored-events/${year}/${month}/${day}/${hour}/${messageId}.json`;
}

async function archiveEvent(record) {
  const bucketName = process.env.ARCHIVE_BUCKET_NAME;
  if (!bucketName) {
    logger.error('ARCHIVE_BUCKET_NAME not set');
    return { success: false, error: 'Archive bucket not configured' };
  }

  try {
    const body = JSON.parse(record.body);
    const timestamp = body.timestamp || new Date().toISOString();
    const messageId = record.messageId;

    const archivedEvent = {
      message_id: messageId,
      archived_at: new Date().toISOString(),
      original_timestamp: timestamp,
      event_data: body.event_data,
      reason: body.reason,
      sqs_attributes: record.attributes || {}
    };

    const s3Key = buildS3Key(timestamp, messageId);

    await getS3Client().send(new PutObjectCommand({
      Bucket: bucketName,
      Key: s3Key,
      Body: JSON.stringify(archivedEvent, null, 2),
      ContentType: 'application/json'
    }));

    logger.info('Archived event to S3:', s3Key);
    return { success: true, key: s3Key };
  } catch (err) {
    logger.error('Failed to archive event:', err.message);
    return { success: false, error: err.message };
  }
}

exports.handler = async (event, _context) => {
  const startTime = Date.now();
  logger.info('Received event:', JSON.stringify(event));

  const records = event.Records || [];
  if (records.length === 0) {
    logger.warn('No records in event');
    return { statusCode: 200, body: JSON.stringify({ message: 'No records to process' }) };
  }

  logger.info('Archiving', records.length, 'ignored event(s) to S3');

  const results = [];
  for (const record of records) {
    const result = await archiveEvent(record);
    results.push(result);
  }

  const elapsed = Date.now() - startTime;
  await publishMetric('ProcessingTime', elapsed, 'Milliseconds');
  await publishMetric('EventsArchived', results.filter(r => r.success).length, 'Count');

  const successCount = results.filter(r => r.success).length;
  const failCount = results.filter(r => !r.success).length;

  logger.info('Archived', successCount, 'event(s) successfully,', failCount, 'failed');

  if (failCount > 0) {
    await publishMetric('ArchiveErrors', failCount, 'Count');
    throw new Error(`${failCount} event(s) failed to archive`);
  }

  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Archived',
      count: records.length,
      success: successCount,
      failed: failCount
    })
  };
};

module.exports = {
  handler: exports.handler,
  archiveEvent,
  buildS3Key
};

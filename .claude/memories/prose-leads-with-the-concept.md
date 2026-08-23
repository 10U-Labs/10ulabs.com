# Prose leads with the concept

Everything written here is read by somebody who was not in the conversation that produced it and does not have the files open. That covers an issue, a commit message, a comment on an issue and a reply in the session. Write for that reader.

Lead with what the thing is for. A paragraph opens by saying what the thing is and what it does, before any file, function or line is named. Say what a defect costs in ordinary words near the top rather than in the seventh paragraph. Opening with the concept is not a licence to re-establish context the reader already has; leading and restating are different things.

Write in concepts, not identifiers. Say what the code does and what goes wrong in plain words, without hedging. An argument about behaviour that only holds while the reader is looking at the file is one the reader cannot check. Identifiers belong where the reader has stopped reading and started working: the change being proposed, the file to edit, the function to delete.

One idea to a sentence. Do not chain subordinate clauses to fit a second idea in. This replaced an older rule that asked for simple, plain, ordinary English, which turned out to constrain vocabulary and say nothing at all about length. It was satisfied for a long time by long clause-chained sentences built out of short words. A rule about the shape of a sentence is refusable in a way an adjective is not.

A detail that changes nothing the reader would do is cut, table or not. A word budget was tried and dropped, because length was never the defect and density is. A cap punishes writing that genuinely needs the words and invites padding what does not.

Tables are allowed where a table genuinely reads better than a paragraph: a name-to-name rename mapping, or two measured columns being compared. Bullets are allowed only when enumerating a list of things. Do not use bullets to break up an argument — an argument is prose.

Nothing here is hard-wrapped — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). How these rules land on the six sections of an issue, and which section carries the identifiers, is in [how-issues-are-written](how-issues-are-written.md).

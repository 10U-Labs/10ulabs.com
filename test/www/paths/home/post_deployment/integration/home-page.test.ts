import { describe, it, expect, beforeAll } from "vitest";

const getBaseUrl = (): string => {
  const envUrl = process.env.BASE_URL;
  const result = envUrl && envUrl.startsWith("http") ? envUrl : "https://10ulabs.com";
  return result;
};

const BASE_URL = getBaseUrl();

interface FetchResponse {
  status: number;
  headers: Headers;
  text: string;
}

let homePageResponse: FetchResponse;

beforeAll(async () => {
  const response = await fetch(BASE_URL, { redirect: "follow" });
  homePageResponse = {
    status: response.status,
    headers: response.headers,
    text: await response.text(),
  };
});

describe("home page", () => {
  describe("response", () => {
    it("returns 200 status", () => {
      const statusIs200 = homePageResponse.status === 200;
      expect(statusIs200).toBe(true);
    });

    it("returns html content type", () => {
      const contentType = homePageResponse.headers.get("content-type") || "";
      const isHtml = contentType.includes("text/html");
      expect(isHtml).toBe(true);
    });

    it("has content", () => {
      const hasContent = homePageResponse.text.length > 0;
      expect(hasContent).toBe(true);
    });
  });

  describe("html structure", () => {
    it("contains doctype", () => {
      const hasDoctype = homePageResponse.text.includes("<!doctype html>");
      expect(hasDoctype).toBe(true);
    });

    it("contains html tag with lang attribute", () => {
      const hasHtmlLang = homePageResponse.text.includes('<html lang="en">');
      expect(hasHtmlLang).toBe(true);
    });

    it("contains title with company name", () => {
      const hasTitle = homePageResponse.text.includes("<title>10U Labs");
      expect(hasTitle).toBe(true);
    });

    it("contains root div for React app", () => {
      const hasRootDiv = homePageResponse.text.includes('id="root"');
      expect(hasRootDiv).toBe(true);
    });

    it("contains javascript bundle", () => {
      const hasJsBundle = homePageResponse.text.includes('type="module"');
      expect(hasJsBundle).toBe(true);
    });

    it("contains css stylesheet", () => {
      const hasCss = homePageResponse.text.includes('rel="stylesheet"');
      expect(hasCss).toBe(true);
    });
  });
});

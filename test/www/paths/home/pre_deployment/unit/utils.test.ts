import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

describe("cn", () => {
  describe("basic functionality", () => {
    it("returns empty string for no arguments", () => {
      const result = cn();
      const isEmpty = result === "";
      expect(isEmpty).toBe(true);
    });

    it("returns single class name unchanged", () => {
      const result = cn("foo");
      const isCorrect = result === "foo";
      expect(isCorrect).toBe(true);
    });

    it("combines multiple class names", () => {
      const result = cn("foo", "bar");
      const hasAllClasses = result.includes("foo") && result.includes("bar");
      expect(hasAllClasses).toBe(true);
    });
  });

  describe("conditional classes", () => {
    it("includes truthy conditional class", () => {
      const isActive = true;
      const result = cn("base", isActive && "active");
      const hasActiveClass = result.includes("active");
      expect(hasActiveClass).toBe(true);
    });

    it("excludes falsy conditional class", () => {
      const isActive = false;
      const result = cn("base", isActive && "active");
      const lacksActiveClass = !result.includes("active");
      expect(lacksActiveClass).toBe(true);
    });

    it("handles undefined values", () => {
      const result = cn("base", undefined, "end");
      const hasBaseAndEnd = result.includes("base") && result.includes("end");
      expect(hasBaseAndEnd).toBe(true);
    });

    it("handles null values", () => {
      const result = cn("base", null, "end");
      const hasBaseAndEnd = result.includes("base") && result.includes("end");
      expect(hasBaseAndEnd).toBe(true);
    });
  });

  describe("tailwind merge", () => {
    it("merges conflicting padding classes", () => {
      const result = cn("p-4", "p-2");
      const hasMergedPadding = result === "p-2";
      expect(hasMergedPadding).toBe(true);
    });

    it("merges conflicting margin classes", () => {
      const result = cn("m-4", "m-8");
      const hasMergedMargin = result === "m-8";
      expect(hasMergedMargin).toBe(true);
    });

    it("merges conflicting text color classes", () => {
      const result = cn("text-red-500", "text-blue-500");
      const hasMergedColor = result === "text-blue-500";
      expect(hasMergedColor).toBe(true);
    });

    it("preserves non-conflicting classes", () => {
      const result = cn("p-4", "m-2", "text-red-500");
      const hasAllClasses = result.includes("p-4") && result.includes("m-2") && result.includes("text-red-500");
      expect(hasAllClasses).toBe(true);
    });
  });

  describe("object syntax", () => {
    it("includes classes with truthy object values", () => {
      const result = cn({ active: true, disabled: false });
      const hasOnlyActive = result.includes("active") && !result.includes("disabled");
      expect(hasOnlyActive).toBe(true);
    });

    it("combines string and object syntax", () => {
      const result = cn("base", { active: true });
      const hasBothClasses = result.includes("base") && result.includes("active");
      expect(hasBothClasses).toBe(true);
    });
  });

  describe("array syntax", () => {
    it("flattens array of class names", () => {
      const result = cn(["foo", "bar"]);
      const hasBothClasses = result.includes("foo") && result.includes("bar");
      expect(hasBothClasses).toBe(true);
    });

    it("handles nested arrays", () => {
      const result = cn(["foo", ["bar", "baz"]]);
      const hasAllClasses = result.includes("foo") && result.includes("bar") && result.includes("baz");
      expect(hasAllClasses).toBe(true);
    });
  });
});

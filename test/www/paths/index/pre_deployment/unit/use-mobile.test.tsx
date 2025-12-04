import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIsMobile } from "@/hooks/use-mobile";

describe("useIsMobile", () => {
  let addEventListenerSpy: ReturnType<typeof vi.fn>;
  let removeEventListenerSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    addEventListenerSpy = vi.fn();
    removeEventListenerSpy = vi.fn();

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: addEventListenerSpy,
        removeEventListener: removeEventListenerSpy,
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initial state", () => {
    it("returns false for desktop width", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 1024 });
      const { result } = renderHook(() => useIsMobile());
      const isNotMobile = result.current === false;
      expect(isNotMobile).toBe(true);
    });

    it("returns true for mobile width", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 500 });
      const { result } = renderHook(() => useIsMobile());
      const isMobile = result.current === true;
      expect(isMobile).toBe(true);
    });

    it("returns false at exactly breakpoint width", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 768 });
      const { result } = renderHook(() => useIsMobile());
      const isNotMobile = result.current === false;
      expect(isNotMobile).toBe(true);
    });

    it("returns true just below breakpoint", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 767 });
      const { result } = renderHook(() => useIsMobile());
      const isMobile = result.current === true;
      expect(isMobile).toBe(true);
    });
  });

  describe("event listener", () => {
    it("adds change event listener on mount", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 1024 });
      renderHook(() => useIsMobile());
      const listenerAdded = addEventListenerSpy.mock.calls.length === 1;
      expect(listenerAdded).toBe(true);
    });

    it("removes change event listener on unmount", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 1024 });
      const { unmount } = renderHook(() => useIsMobile());
      unmount();
      const listenerRemoved = removeEventListenerSpy.mock.calls.length === 1;
      expect(listenerRemoved).toBe(true);
    });
  });

  describe("responsive updates", () => {
    it("updates when window resizes to mobile", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 1024 });
      const { result } = renderHook(() => useIsMobile());
      act(() => {
        Object.defineProperty(window, "innerWidth", { writable: true, value: 500 });
        const changeHandler = addEventListenerSpy.mock.calls[0][1];
        changeHandler();
      });
      const isMobile = result.current === true;
      expect(isMobile).toBe(true);
    });

    it("updates when window resizes to desktop", () => {
      Object.defineProperty(window, "innerWidth", { writable: true, value: 500 });
      const { result } = renderHook(() => useIsMobile());
      act(() => {
        Object.defineProperty(window, "innerWidth", { writable: true, value: 1024 });
        const changeHandler = addEventListenerSpy.mock.calls[0][1];
        changeHandler();
      });
      const isNotMobile = result.current === false;
      expect(isNotMobile).toBe(true);
    });
  });
});

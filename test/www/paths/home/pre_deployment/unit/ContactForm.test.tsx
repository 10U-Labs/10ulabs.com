import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "./utils";
import userEvent from "@testing-library/user-event";
import { ContactForm } from "@/components/ContactForm";

const mockToast = vi.fn();

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

vi.mock("@/hooks/use_toast", () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe("ContactForm", () => {
  describe("rendering", () => {
    it("renders name input", () => {
      render(<ContactForm />);
      const nameInputExists = screen.getByPlaceholderText("Name *") !== null;
      expect(nameInputExists).toBe(true);
    });

    it("renders email input", () => {
      render(<ContactForm />);
      const emailInputExists = screen.getByPlaceholderText("Email *") !== null;
      expect(emailInputExists).toBe(true);
    });

    it("renders message textarea", () => {
      render(<ContactForm />);
      const messageInputExists = screen.getByPlaceholderText("Message *") !== null;
      expect(messageInputExists).toBe(true);
    });

    it("renders submit button", () => {
      render(<ContactForm />);
      const buttonExists = screen.getByRole("button", { name: "Send Message" }) !== null;
      expect(buttonExists).toBe(true);
    });
  });

  describe("input handling", () => {
    it("updates name field on input", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const nameInput = screen.getByPlaceholderText("Name *");
      await user.type(nameInput, "John Doe");
      const valueMatches = (nameInput as HTMLInputElement).value === "John Doe";
      expect(valueMatches).toBe(true);
    });

    it("updates email field on input", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const emailInput = screen.getByPlaceholderText("Email *");
      await user.type(emailInput, "john@example.com");
      const valueMatches = (emailInput as HTMLInputElement).value === "john@example.com";
      expect(valueMatches).toBe(true);
    });

    it("updates message field on input", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const messageInput = screen.getByPlaceholderText("Message *");
      await user.type(messageInput, "Hello there");
      const valueMatches = (messageInput as HTMLTextAreaElement).value === "Hello there";
      expect(valueMatches).toBe(true);
    });
  });

  describe("validation", () => {
    beforeEach(() => {
      vi.stubGlobal("grecaptcha", {
        ready: (cb: () => void) => cb(),
        execute: () => Promise.resolve("test-token"),
      });
    });

    it("shows error for empty name on submit", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const emailInput = screen.getByPlaceholderText("Email *");
      const messageInput = screen.getByPlaceholderText("Message *");
      await user.type(emailInput, "test@example.com");
      await user.type(messageInput, "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      const errorVisible = await screen.findByText("Name is required");
      expect(errorVisible !== null).toBe(true);
    });

    it("shows error for empty message on submit", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const nameInput = screen.getByPlaceholderText("Name *");
      const emailInput = screen.getByPlaceholderText("Email *");
      await user.type(nameInput, "John Doe");
      await user.type(emailInput, "test@example.com");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      const errorVisible = await screen.findByText("Message is required");
      expect(errorVisible !== null).toBe(true);
    });
  });

  describe("submit button state", () => {
    it("button is enabled by default", () => {
      render(<ContactForm />);
      const button = screen.getByRole("button", { name: "Send Message" });
      const isEnabled = !button.hasAttribute("disabled");
      expect(isEnabled).toBe(true);
    });
  });

  describe("email input", () => {
    it("email input has correct type attribute", () => {
      render(<ContactForm />);
      const emailInput = screen.getByPlaceholderText("Email *");
      const hasEmailType = emailInput.getAttribute("type") === "email";
      expect(hasEmailType).toBe(true);
    });
  });

  describe("successful submission", () => {
    beforeEach(() => {
      mockToast.mockClear();
      vi.stubGlobal("grecaptcha", {
        ready: (cb: () => void) => cb(),
        execute: () => Promise.resolve("test-token"),
      });
      vi.stubGlobal("fetch", vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        })
      ));
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("clears form after successful submission", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const nameInput = screen.getByPlaceholderText("Name *") as HTMLInputElement;
      const emailInput = screen.getByPlaceholderText("Email *") as HTMLInputElement;
      const messageInput = screen.getByPlaceholderText("Message *") as HTMLTextAreaElement;
      await user.type(nameInput, "John Doe");
      await user.type(emailInput, "john@example.com");
      await user.type(messageInput, "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      await waitFor(() => {
        const formCleared = nameInput.value === "" && emailInput.value === "" && messageInput.value === "";
        expect(formCleared).toBe(true);
      });
    });

    it("shows success toast after submission", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      await user.type(screen.getByPlaceholderText("Name *"), "John Doe");
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      await waitFor(() => {
        const toastCalled = mockToast.mock.calls.length > 0;
        expect(toastCalled).toBe(true);
      });
    });
  });

  describe("API error handling", () => {
    beforeEach(() => {
      mockToast.mockClear();
      vi.stubGlobal("grecaptcha", {
        ready: (cb: () => void) => cb(),
        execute: () => Promise.resolve("test-token"),
      });
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("shows error toast when API returns error", async () => {
      vi.stubGlobal("fetch", vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ error: "Server error" }),
        })
      ));
      const user = userEvent.setup();
      render(<ContactForm />);
      await user.type(screen.getByPlaceholderText("Name *"), "John Doe");
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      await waitFor(() => {
        const errorToastShown = mockToast.mock.calls.some(
          (call) => call[0]?.variant === "destructive"
        );
        expect(errorToastShown).toBe(true);
      });
    });

    it("shows default error message when API returns no error details", async () => {
      vi.stubGlobal("fetch", vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.reject(new Error("Parse error")),
        })
      ));
      const user = userEvent.setup();
      render(<ContactForm />);
      await user.type(screen.getByPlaceholderText("Name *"), "John Doe");
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      await waitFor(() => {
        const toastWasCalled = mockToast.mock.calls.length > 0;
        expect(toastWasCalled).toBe(true);
      });
    });
  });

  describe("reCAPTCHA behavior", () => {
    beforeEach(() => {
      mockToast.mockClear();
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("shows error when reCAPTCHA fails to load", async () => {
      vi.stubGlobal("grecaptcha", undefined);
      const user = userEvent.setup();
      render(<ContactForm />);
      await user.type(screen.getByPlaceholderText("Name *"), "John Doe");
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      await waitFor(() => {
        const errorToastShown = mockToast.mock.calls.some(
          (call) => call[0]?.variant === "destructive"
        );
        expect(errorToastShown).toBe(true);
      });
    });
  });

  describe("field length validation", () => {
    beforeEach(() => {
      vi.stubGlobal("grecaptcha", {
        ready: (cb: () => void) => cb(),
        execute: () => Promise.resolve("test-token"),
      });
    });

    it("shows error when name exceeds max length", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const longName = "a".repeat(101);
      await user.type(screen.getByPlaceholderText("Name *"), longName);
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), "Test message");
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      const errorVisible = await screen.findByText("Name must be less than 100 characters");
      expect(errorVisible !== null).toBe(true);
    });

    it("shows error when message exceeds max length", async () => {
      const user = userEvent.setup();
      render(<ContactForm />);
      const longMessage = "a".repeat(1001);
      await user.type(screen.getByPlaceholderText("Name *"), "John Doe");
      await user.type(screen.getByPlaceholderText("Email *"), "john@example.com");
      await user.type(screen.getByPlaceholderText("Message *"), longMessage);
      await user.click(screen.getByRole("button", { name: "Send Message" }));
      const errorVisible = await screen.findByText("Message must be less than 1000 characters");
      expect(errorVisible !== null).toBe(true);
    });
  });
});

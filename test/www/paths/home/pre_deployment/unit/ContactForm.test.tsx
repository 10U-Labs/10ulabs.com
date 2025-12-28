import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "./utils";
import userEvent from "@testing-library/user-event";
import { ContactForm } from "@/components/ContactForm";

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
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
});

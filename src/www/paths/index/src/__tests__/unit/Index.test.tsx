import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@/__tests__/unit/utils";
import Index from "@/pages/Index";

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("Index", () => {
  describe("hero section", () => {
    it("renders company name", () => {
      render(<Index />);
      const companyNameExists = screen.getByText("10U Labs, LLC") !== null;
      expect(companyNameExists).toBe(true);
    });

    it("renders tagline", () => {
      render(<Index />);
      const taglineExists = screen.getByText("Building flexible computing hardware for diverse environments") !== null;
      expect(taglineExists).toBe(true);
    });

    it("renders get in touch button", () => {
      render(<Index />);
      const buttonExists = screen.getByRole("button", { name: "Get in Touch" }) !== null;
      expect(buttonExists).toBe(true);
    });

    it("renders our products button", () => {
      render(<Index />);
      const buttonExists = screen.getByRole("button", { name: "Our Products" }) !== null;
      expect(buttonExists).toBe(true);
    });
  });

  describe("products section", () => {
    it("renders section heading", () => {
      render(<Index />);
      const headingExists = screen.getByText("Our Focus Areas") !== null;
      expect(headingExists).toBe(true);
    });

    it("renders CPUs card", () => {
      render(<Index />);
      const cardExists = screen.getByText("CPUs") !== null;
      expect(cardExists).toBe(true);
    });

    it("renders CPU Sockets card", () => {
      render(<Index />);
      const cardExists = screen.getByText("CPU Sockets") !== null;
      expect(cardExists).toBe(true);
    });

    it("renders Motherboards card", () => {
      render(<Index />);
      const cardExists = screen.getByText("Motherboards") !== null;
      expect(cardExists).toBe(true);
    });
  });

  describe("about section", () => {
    it("renders about heading", () => {
      render(<Index />);
      const headingExists = screen.getByText("About 10U Labs") !== null;
      expect(headingExists).toBe(true);
    });
  });

  describe("contact section", () => {
    it("renders contact heading", () => {
      render(<Index />);
      const headingExists = screen.getByText("Contact Us") !== null;
      expect(headingExists).toBe(true);
    });

    it("renders contact form", () => {
      render(<Index />);
      const formExists = screen.getByPlaceholderText("Name *") !== null;
      expect(formExists).toBe(true);
    });
  });

  describe("footer", () => {
    it("renders copyright notice", () => {
      render(<Index />);
      const copyrightExists = screen.getByText(/Copyright © 2025 10U Labs, LLC/) !== null;
      expect(copyrightExists).toBe(true);
    });

    it("renders privacy notice link", () => {
      render(<Index />);
      const linkExists = screen.getByRole("link", { name: "Privacy Notice" }) !== null;
      expect(linkExists).toBe(true);
    });
  });
});

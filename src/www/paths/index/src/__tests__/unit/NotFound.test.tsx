import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NotFound from "@/pages/NotFound";

const futureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};

describe("NotFound", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  describe("rendering", () => {
    it("renders 404 heading", () => {
      render(
        <MemoryRouter initialEntries={["/invalid-path"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const headingExists = screen.getByText("404") !== null;
      expect(headingExists).toBe(true);
    });

    it("renders error message", () => {
      render(
        <MemoryRouter initialEntries={["/invalid-path"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const messageExists = screen.getByText("Oops! Page not found") !== null;
      expect(messageExists).toBe(true);
    });

    it("renders return home link", () => {
      render(
        <MemoryRouter initialEntries={["/invalid-path"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const linkExists = screen.getByRole("link", { name: "Return to Home" }) !== null;
      expect(linkExists).toBe(true);
    });

    it("home link points to root", () => {
      render(
        <MemoryRouter initialEntries={["/invalid-path"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const link = screen.getByRole("link", { name: "Return to Home" });
      const hasCorrectHref = link.getAttribute("href") === "/";
      expect(hasCorrectHref).toBe(true);
    });
  });

  describe("logging", () => {
    it("logs error on mount", () => {
      render(
        <MemoryRouter initialEntries={["/invalid-path"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const errorWasLogged = consoleErrorSpy.mock.calls.length === 1;
      expect(errorWasLogged).toBe(true);
    });

    it("logs the attempted path", () => {
      render(
        <MemoryRouter initialEntries={["/some-invalid-route"]} future={futureFlags}>
          <NotFound />
        </MemoryRouter>
      );
      const loggedPath = consoleErrorSpy.mock.calls[0][1] === "/some-invalid-route";
      expect(loggedPath).toBe(true);
    });
  });
});

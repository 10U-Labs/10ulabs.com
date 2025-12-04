import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { NavLink } from "@/components/NavLink";

const futureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};

const renderNavLink = (initialPath: string, linkTo: string, props: Record<string, string> = {}) => {
  render(
    <MemoryRouter initialEntries={[initialPath]} future={futureFlags}>
      <Routes>
        <Route
          path="*"
          element={
            <NavLink to={linkTo} {...props}>
              Test Link
            </NavLink>
          }
        />
      </Routes>
    </MemoryRouter>
  );
};

describe("NavLink", () => {
  describe("rendering", () => {
    it("renders link text", () => {
      renderNavLink("/", "/about");
      const linkExists = screen.getByText("Test Link") !== null;
      expect(linkExists).toBe(true);
    });

    it("renders as anchor element", () => {
      renderNavLink("/", "/about");
      const isAnchor = screen.getByText("Test Link").tagName === "A";
      expect(isAnchor).toBe(true);
    });

    it("has correct href attribute", () => {
      renderNavLink("/", "/about");
      const link = screen.getByText("Test Link");
      const hasCorrectHref = link.getAttribute("href") === "/about";
      expect(hasCorrectHref).toBe(true);
    });
  });

  describe("className handling", () => {
    it("applies base className", () => {
      renderNavLink("/", "/about", { className: "base-class" });
      const link = screen.getByText("Test Link");
      const hasBaseClass = link.classList.contains("base-class");
      expect(hasBaseClass).toBe(true);
    });

    it("applies activeClassName when route matches", () => {
      renderNavLink("/about", "/about", { className: "base-class", activeClassName: "active-class" });
      const link = screen.getByText("Test Link");
      const hasActiveClass = link.classList.contains("active-class");
      expect(hasActiveClass).toBe(true);
    });

    it("does not apply activeClassName when route does not match", () => {
      renderNavLink("/home", "/about", { className: "base-class", activeClassName: "active-class" });
      const link = screen.getByText("Test Link");
      const lacksActiveClass = !link.classList.contains("active-class");
      expect(lacksActiveClass).toBe(true);
    });
  });
});

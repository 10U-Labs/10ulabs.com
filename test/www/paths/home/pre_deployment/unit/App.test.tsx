import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "@/pages/Index";
import NotFound from "@/pages/NotFound";

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock("@/hooks/use_toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const futureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

interface TestWrapperProps {
  children: React.ReactNode;
  initialPath?: string;
}

const TestWrapper = ({ children, initialPath = "/" }: TestWrapperProps) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <MemoryRouter initialEntries={[initialPath]} future={futureFlags}>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

describe("App", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeAll(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  describe("routing", () => {
    it("renders Index page for root path", async () => {
      render(<TestWrapper initialPath="/" />);
      await waitFor(() => {
        const companyNameExists = screen.getByText("10U Labs, LLC") !== null;
        expect(companyNameExists).toBe(true);
      });
    });

    it("renders NotFound page for invalid path", async () => {
      render(<TestWrapper initialPath="/invalid-path-that-does-not-exist" />);
      await waitFor(() => {
        const notFoundExists = screen.getByText("404") !== null;
        expect(notFoundExists).toBe(true);
      });
    });
  });

  describe("route structure", () => {
    it("has root route for Index", () => {
      render(<TestWrapper initialPath="/" />);
      const hasIndexContent = screen.getByText("10U Labs, LLC") !== null;
      expect(hasIndexContent).toBe(true);
    });

    it("has catch-all route for NotFound", () => {
      render(<TestWrapper initialPath="/nonexistent" />);
      const hasNotFoundContent = screen.getByText("404") !== null;
      expect(hasNotFoundContent).toBe(true);
    });
  });
});

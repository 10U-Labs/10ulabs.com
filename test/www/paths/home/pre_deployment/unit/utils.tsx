import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ReactElement, ReactNode } from "react";

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

interface WrapperProps {
  children: ReactNode;
}

const AllProviders = ({ children }: WrapperProps) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter future={futureFlags}>{children}</BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export const createMemoryRouterWrapper = (initialEntries: string[] = ["/"]) => {
  const MemoryRouterWrapper = ({ children }: { children: ReactNode }) => {
    const queryClient = createTestQueryClient();
    return (
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <MemoryRouter initialEntries={initialEntries} future={futureFlags}>{children}</MemoryRouter>
        </TooltipProvider>
      </QueryClientProvider>
    );
  };
  return MemoryRouterWrapper;
};

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) =>
  render(ui, { wrapper: AllProviders, ...options });

export * from "@testing-library/react";
export { customRender as render };

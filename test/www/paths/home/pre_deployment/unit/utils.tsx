import { render, RenderOptions } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ReactElement, ReactNode } from "react";

import { AllProviders } from "./providers";
import { createTestQueryClient, futureFlags } from "./provider_defaults";

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

export { screen, waitFor } from "@testing-library/react";
export { customRender as render };

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ReactNode } from "react";

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

export const AllProviders = ({ children }: { children: ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter future={futureFlags}>{children}</BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

import { QueryClient } from "@tanstack/react-query";

export const futureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

import { render, RenderOptions } from "@testing-library/react";
import { ReactElement } from "react";

import { AllProviders } from "./providers";

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) =>
  render(ui, { wrapper: AllProviders, ...options });

export { screen, waitFor } from "@testing-library/react";
export { customRender as render };

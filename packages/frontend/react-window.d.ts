// Type declarations for react-window (compatible with React 19)
// Temporary shim — delete when migrating to react-window 2.x, which ships its own types.
/* eslint-disable @typescript-eslint/no-explicit-any */
declare module "react-window" {
  import { ComponentType, CSSProperties } from "react";

  export interface ListChildComponentProps {
    index: number;
    style: CSSProperties;
    data?: any;
  }

  export interface FixedSizeListProps {
    children: ComponentType<ListChildComponentProps>;
    className?: string;
    height: number | string;
    itemCount: number;
    itemData?: any;
    itemSize: number;
    width: number | string;
  }

  export const FixedSizeList: ComponentType<FixedSizeListProps>;
}

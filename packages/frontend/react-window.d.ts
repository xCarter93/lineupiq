// Type declarations for react-window (compatible with React 19)
declare module "react-window" {
  import { ComponentType, CSSProperties, ReactElement } from "react";

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

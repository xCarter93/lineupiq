"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";

type SidebarState = "expanded" | "collapsed" | "hidden";

interface SidebarContextType {
  state: SidebarState;
  isExpanded: boolean;
  isCollapsed: boolean;
  isHidden: boolean;
  isMobile: boolean;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
  toggle: () => void;
  expand: () => void;
  collapse: () => void;
}

const SidebarContext = createContext<SidebarContextType | null>(null);

const MOBILE_BREAKPOINT = 768;
const TABLET_BREAKPOINT = 1024;

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SidebarState>("expanded");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Handle responsive breakpoints
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < MOBILE_BREAKPOINT) {
        setState("hidden");
        setIsMobile(true);
      } else if (width < TABLET_BREAKPOINT) {
        setState("collapsed");
        setIsMobile(false);
      } else {
        setState("expanded");
        setIsMobile(false);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggle = useCallback(() => {
    setState((prev) => (prev === "expanded" ? "collapsed" : "expanded"));
  }, []);

  const expand = useCallback(() => {
    setState("expanded");
  }, []);

  const collapse = useCallback(() => {
    setState("collapsed");
  }, []);

  const value: SidebarContextType = {
    state,
    isExpanded: state === "expanded",
    isCollapsed: state === "collapsed",
    isHidden: state === "hidden",
    isMobile,
    mobileOpen,
    setMobileOpen,
    toggle,
    expand,
    collapse,
  };

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}

"use client";

import { Menu, X, PanelLeftClose, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { useSidebar, SidebarProvider } from "./sidebar-context";
import { SidebarNav } from "./SidebarNav";
import { SidebarLineupPreview } from "./SidebarLineupPreview";
import { SidebarRecentPlayers } from "./SidebarRecentPlayers";
import { SidebarSimulationStatus } from "./SidebarSimulationStatus";
import Link from "next/link";

const SIDEBAR_WIDTH = 250;
const SIDEBAR_COLLAPSED_WIDTH = 64;

function SidebarLogo() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex items-center h-16 px-4">
      <Link
        href="/"
        className="flex items-center gap-2 font-bold text-lg tracking-tight text-foreground hover:text-primary transition-colors"
      >
        <span className="text-primary text-2xl">IQ</span>
        {!isCollapsed && <span>LineupIQ</span>}
      </Link>
    </div>
  );
}

function SidebarToggle() {
  const { isCollapsed, toggle } = useSidebar();

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggle}
      className="absolute -right-3 top-6 z-10 h-6 w-6 rounded-full border bg-background shadow-sm hover:bg-accent"
    >
      {isCollapsed ? (
        <PanelLeft className="h-3 w-3" />
      ) : (
        <PanelLeftClose className="h-3 w-3" />
      )}
      <span className="sr-only">Toggle sidebar</span>
    </Button>
  );
}

function MobileMenuButton() {
  const { mobileOpen, setMobileOpen } = useSidebar();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setMobileOpen(!mobileOpen)}
      className="md:hidden"
    >
      {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      <span className="sr-only">Toggle menu</span>
    </Button>
  );
}

function SidebarContent() {
  return (
    <div className="flex flex-col h-full">
      <SidebarLogo />
      <Separator className="bg-sidebar-border" />

      {/* Simulation Status (when active) */}
      <SidebarSimulationStatus />

      {/* Navigation */}
      <div className="flex-1 py-4 overflow-y-auto">
        <SidebarNav />

        <Separator className="my-4 bg-sidebar-border" />

        {/* Lineup Preview */}
        <SidebarLineupPreview />

        <Separator className="my-4 bg-sidebar-border" />

        {/* Recent Players */}
        <SidebarRecentPlayers />
      </div>
    </div>
  );
}

function DesktopSidebar() {
  const { isCollapsed, isHidden } = useSidebar();

  if (isHidden) {
    return null;
  }

  return (
    <aside
      className={cn(
        "relative hidden md:flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-in-out",
        isCollapsed ? "w-16" : "w-[250px]"
      )}
      style={{
        width: isCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
      }}
    >
      <SidebarToggle />
      <SidebarContent />
    </aside>
  );
}

function MobileSidebar() {
  const { mobileOpen, setMobileOpen } = useSidebar();

  return (
    <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
      <SheetContent side="left" className="w-[250px] p-0" showCloseButton={false}>
        <SidebarContent />
      </SheetContent>
    </Sheet>
  );
}

function MobileHeader() {
  const { isHidden } = useSidebar();

  if (!isHidden) {
    return null;
  }

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-background px-4 md:hidden">
      <MobileMenuButton />
      <Link
        href="/"
        className="flex items-center gap-2 font-bold text-lg tracking-tight"
      >
        <span className="text-primary">IQ</span>
        <span>LineupIQ</span>
      </Link>
    </header>
  );
}

interface SidebarLayoutProps {
  children: React.ReactNode;
}

export function SidebarLayout({ children }: SidebarLayoutProps) {
  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden">
        <DesktopSidebar />
        <MobileSidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <MobileHeader />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
}

export { MobileMenuButton };

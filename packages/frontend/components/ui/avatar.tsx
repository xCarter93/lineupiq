"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface AvatarProps {
  src?: string;
  alt: string;
  fallback: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-14 h-14 text-base",
};

/**
 * Avatar component for displaying player headshots with fallback support.
 *
 * Shows an image when `src` is provided, falls back to initials on error or when no image.
 */
export function Avatar({
  src,
  alt,
  fallback,
  size = "md",
  className,
}: AvatarProps) {
  const [hasError, setHasError] = React.useState(false);

  // Reset error state when src changes
  React.useEffect(() => {
    setHasError(false);
  }, [src]);

  const handleImageError = () => {
    setHasError(true);
  };

  const showFallback = !src || hasError;

  return (
    <div
      className={cn(
        "relative rounded-full overflow-hidden bg-muted flex items-center justify-center",
        sizeClasses[size],
        className
      )}
      role="img"
      aria-label={alt}
    >
      {showFallback ? (
        <span className="text-muted-foreground font-medium">{fallback}</span>
      ) : (
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover"
          onError={handleImageError}
        />
      )}
    </div>
  );
}

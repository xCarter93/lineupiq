"use client";

import {
  NumberField,
  NumberFieldDecrement,
  NumberFieldGroup,
  NumberFieldIncrement,
  NumberFieldInput,
  NumberFieldScrubArea,
} from "@/components/reui/number-field";
import { cn } from "@/lib/utils";

interface StatInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  disabled?: boolean;
}

export function StatInput({
  label,
  value,
  onChange,
  suffix,
  min,
  max,
  step = 1,
  className,
  disabled = false,
}: StatInputProps) {
  return (
    <NumberField
      value={value}
      onValueChange={(next) => onChange(next ?? 0)}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      className={cn("gap-1.5", className)}
    >
      <NumberFieldScrubArea label={label} className="text-muted-foreground" />
      <div className="flex items-center gap-2">
        <NumberFieldGroup className="w-28">
          <NumberFieldDecrement />
          <NumberFieldInput />
          <NumberFieldIncrement />
        </NumberFieldGroup>
        {suffix && (
          <span className="text-xs text-muted-foreground">{suffix}</span>
        )}
      </div>
    </NumberField>
  );
}

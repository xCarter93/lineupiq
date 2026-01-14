import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Page() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-primary">
            LineupIQ
          </CardTitle>
          <CardDescription className="text-base">
            Fantasy Football Predictions
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-4">
          <p className="text-center text-muted-foreground">
            Matchup simulator coming soon
          </p>
          <Button size="lg">Get Started</Button>
        </CardContent>
      </Card>
    </div>
  );
}
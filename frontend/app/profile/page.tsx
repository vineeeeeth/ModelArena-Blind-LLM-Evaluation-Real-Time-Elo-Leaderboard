"use client";

import React from "react";
import { User as UserIcon, Shield, CheckCircle, Mail, Calendar } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useUser } from "@/lib/hooks/use-auth";

export default function ProfilePage() {
  const { data: user, isLoading } = useUser();

  if (isLoading) {
    return <div className="container mx-auto max-w-md py-12 text-center text-muted-foreground">Loading profile...</div>;
  }

  if (!user) {
    return (
      <div className="container mx-auto max-w-md py-12 text-center space-y-4">
        <h2 className="text-xl font-bold">Not Logged In</h2>
        <p className="text-sm text-muted-foreground">Please log in to view your voter profile and history.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-xl px-4 py-12 space-y-6">
      <Card>
        <CardHeader className="text-center pb-2">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <UserIcon className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl mt-3">{user.display_name}</CardTitle>
          <CardDescription className="flex items-center justify-center gap-1.5">
            <Mail className="h-3.5 w-3.5" /> {user.email}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          <div className="flex items-center justify-between py-2 border-b border-border/40 text-sm">
            <span className="text-muted-foreground flex items-center gap-1.5">
              <Shield className="h-4 w-4" /> Role
            </span>
            <Badge variant="outline" className="uppercase text-xs font-mono">
              {user.role}
            </Badge>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-border/40 text-sm">
            <span className="text-muted-foreground flex items-center gap-1.5">
              <CheckCircle className="h-4 w-4" /> Email Verified
            </span>
            <Badge variant={user.is_email_verified ? "secondary" : "outline"} className="text-xs">
              {user.is_email_verified ? "Verified Voter" : "Unverified"}
            </Badge>
          </div>

          <div className="flex items-center justify-between py-2 text-sm">
            <span className="text-muted-foreground flex items-center gap-1.5">
              <Calendar className="h-4 w-4" /> Member Since
            </span>
            <span className="font-mono text-xs text-foreground">
              {new Date(user.created_at).toLocaleDateString()}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


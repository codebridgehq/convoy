import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account and preferences.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-foreground">
            General
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Update your account information.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="org-name" className="text-foreground">
                Organization Name
              </Label>
              <Input
                id="org-name"
                defaultValue="Acme Corp"
                className="bg-background text-foreground"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email" className="text-foreground">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                defaultValue="admin@acme.dev"
                className="bg-background text-foreground"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button>Save Changes</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-foreground">
            Webhook Configuration
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Configure where completed cargo results are delivered.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <Label htmlFor="webhook-url" className="text-foreground">
              Callback URL
            </Label>
            <Input
              id="webhook-url"
              placeholder="https://your-app.com/api/convoy/callback"
              className="bg-background font-mono text-sm text-foreground"
            />
          </div>
          <div className="flex justify-end">
            <Button>Update Webhook</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-destructive">
            Danger Zone
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Irreversible actions that affect your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Separator className="mb-6" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">
                Delete Organization
              </p>
              <p className="text-sm text-muted-foreground">
                Permanently remove your organization and all associated data.
              </p>
            </div>
            <Button variant="destructive" size="sm">
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

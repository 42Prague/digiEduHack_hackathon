"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Container, Title, Text, Card, Group, Stack, Badge, Button, AppShell, Anchor, Avatar, Menu, UnstyledButton, rem } from "@mantine/core";
import { IconLogout, IconChevronDown } from "@tabler/icons-react";
import { api } from "~/trpc/react";
import { authClient } from "~/server/better-auth/client";
import Link from "next/link";
import Image from "next/image";

export default function UserDashboard() {
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const { data: forms, isLoading } = api.forms.listWithStatus.useQuery();
  const { data: session } = authClient.useSession();

  const handleSignOut = async () => {
    setIsLoggingOut(true);
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => {
          router.push("/");
        },
        onError: () => {
          setIsLoggingOut(false);
        },
      },
    });
  };

  const getStatusBadge = (status: string | null) => {
    if (status === "submitted") {
      return <Badge color="green" variant="filled">Odesláno</Badge>;
    }
    if (status === "draft") {
      return <Badge color="yellow" variant="light">Koncept</Badge>;
    }
    return <Badge color="blue" variant="light">Nezahájeno</Badge>;
  };

  const getButtonText = (status: string | null) => {
    if (status === "submitted") {
      return "Zobrazit odeslaný formulář";
    }
    if (status === "draft") {
      return "Pokračovat v konceptu";
    }
    return "Zahájit formulář";
  };

  const renderNavbar = () => (
    <AppShell.Header style={{ borderBottom: '1px solid #e9ecef' }}>
      <Group h="100%" px="md" justify="space-between">
        {/* Logo */}
        <Anchor 
          href="https://www.eduzmena.cz/cs" 
          target="_blank" 
          rel="noopener noreferrer"
          style={{ display: 'flex', alignItems: 'center' }}
        >
          <Image 
            src="/eduzmena-logo.png" 
            alt="Eduzměna" 
            width={120} 
            height={32}
            style={{ objectFit: 'contain' }}
          />
        </Anchor>

        {/* User Info & Sign Out */}
        {session?.user && (
          <Menu shadow="md" width={220}>
            <Menu.Target>
              <UnstyledButton>
                <Group gap="xs">
                  <Avatar 
                    color="blue" 
                    radius="xl" 
                    size="sm"
                  >
                    {session.user.name?.[0]?.toUpperCase() ?? "U"}
                  </Avatar>
                  <div style={{ flex: 1, maxWidth: '150px' }}>
                    <Text size="sm" fw={500} lineClamp={1}>
                      {session.user.name ?? "User"}
                    </Text>
                  </div>
                  <IconChevronDown size={16} style={{ opacity: 0.6 }} />
                </Group>
              </UnstyledButton>
            </Menu.Target>

            <Menu.Dropdown>
              <Menu.Label>Účet</Menu.Label>
              <Menu.Item disabled>
                <Text size="xs" c="dimmed" lineClamp={1}>
                  {session.user.email}
                </Text>
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item 
                color="red"
                leftSection={<IconLogout size={16} />}
                onClick={handleSignOut}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? "Odhlašování..." : "Odhlásit se"}
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        )}
      </Group>
    </AppShell.Header>
  );

  if (isLoading) {
    return (
      <AppShell header={{ height: 60 }}>
        {renderNavbar()}
        <AppShell.Main>
          <Container size="lg" py="xl">
            <Text>Načítání formulářů...</Text>
          </Container>
        </AppShell.Main>
      </AppShell>
    );
  }

  return (
    <AppShell header={{ height: 60 }}>
      {renderNavbar()}
      <AppShell.Main>
        <Container size="lg" py="xl">
          <Stack gap="lg">
            <div>
              <Title order={1} mb="xs">Dostupné formuláře</Title>
              <Text c="dimmed">Vyplňte níže uvedené formuláře</Text>
            </div>

            {forms && forms.length > 0 ? (
              <Stack gap="md">
                {forms.map((form) => (
                  <Card key={form.id} shadow="sm" padding="lg" radius="md" withBorder>
                    <Stack gap="sm">
                      <Group justify="space-between" align="flex-start">
                        <div style={{ flex: 1 }}>
                          <Title order={3} mb="xs">{form.label}</Title>
                          {form.description && (
                            <Text size="sm" c="dimmed">{form.description}</Text>
                          )}
                        </div>
                        {getStatusBadge(form.submissionStatus)}
                      </Group>
                      
                      <Group justify="flex-end">
                        <Button
                          component={Link}
                          href={`/dashboard/forms/${form.id}`}
                          variant={form.submissionStatus === "submitted" ? "light" : "filled"}
                        >
                          {getButtonText(form.submissionStatus)}
                        </Button>
                      </Group>
                    </Stack>
                  </Card>
                ))}
              </Stack>
            ) : (
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Text c="dimmed" ta="center">V tuto chvíli nejsou k dispozici žádné formuláře</Text>
              </Card>
            )}
          </Stack>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
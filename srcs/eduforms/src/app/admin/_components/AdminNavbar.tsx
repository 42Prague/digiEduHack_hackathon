"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  IconDashboard,
  IconUsers,
  IconBuilding,
  IconLogout,
  IconSettings,
  IconForms,
  IconChartBar,
} from "@tabler/icons-react";
import { Stack, NavLink, Avatar, Text, Group, Badge, Divider, Paper } from "@mantine/core";
import { authClient } from "~/server/better-auth/client";

interface LinkItem {
  label: string;
  icon: React.ComponentType<{ size?: number; stroke?: number }>;
  href: string;
}

export function AdminNavbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { data: session } = authClient.useSession();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

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

  const mainLinks: LinkItem[] = [
    { label: "Přehled", icon: IconDashboard, href: "/admin" },
    { label: "Uživatelé", icon: IconUsers, href: "/admin/users" },
    { label: "Instituce", icon: IconBuilding, href: "/admin/institutions" },
    { label: "Formuláře", icon: IconForms, href: "/admin/forms" },
    { label: "Výsledky", icon: IconChartBar, href: "/admin/results" },
  ];

  return (
    <nav className="w-72 bg-white h-screen fixed left-0 top-0 flex flex-col border-r border-gray-200">
      <Stack gap="md" p="md" style={{ height: "100%" }}>
        {/* Header */}
        <div>
          <Group gap="sm">
            <Avatar color="blue" radius="md">E</Avatar>
            <div>
              <Text size="lg" fw={700}>EduForms</Text>
              <Text size="xs" c="dimmed">Administrátorský panel</Text>
            </div>
          </Group>
        </div>

        <Divider />

        

        {/* Navigation Links */}
        <Stack gap={4} style={{ flex: 1 }}>
          <Text size="xs" fw={600} c="dimmed" tt="uppercase" px="xs" mb="xs">
            Navigace
          </Text>
          {mainLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <NavLink
                key={link.label}
                href={link.href}
                label={link.label}
                leftSection={<link.icon size={20} stroke={1.5} />}
                active={isActive}
                onClick={(e) => {
                  e.preventDefault();
                  router.push(link.href);
                }}
              />
            );
          })}

          <Divider my="md" />

        </Stack>
          {/* User Profile */}
        {session?.user && (
          <Paper p="md" withBorder>
            <Group gap="sm" mb="sm">
              <Avatar color="teal" radius="xl">
                {session.user.name?.[0]?.toUpperCase() ?? "A"}
              </Avatar>
              <div style={{ flex: 1 }}>
                <Text size="sm" fw={500} lineClamp={1}>
                  {session.user.name ?? "Administrátor"}
                </Text>
                <Text size="xs" c="dimmed" lineClamp={1}>
                  {session.user.email}
                </Text>
              </div>
            </Group>
            <Badge color="violet" variant="light" fullWidth>
              Administrátor
            </Badge>
          </Paper>
        )}

        {/* Footer with Sign Out */}
        <div>
          <Divider mb="md" />
          <NavLink
            label={isLoggingOut ? "Odhlašování..." : "Odhlásit se"}
            leftSection={<IconLogout size={20} stroke={1.5} />}
            onClick={handleSignOut}
            color="red"
            disabled={isLoggingOut}
          />
          <Text size="xs" c="dimmed" ta="center" mt="md">
            v3.1.2 • © 2025
          </Text>
        </div>
      </Stack>
    </nav>
  );
}

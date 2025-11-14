"use client";

import { Tabs, Container } from "@mantine/core";
import { IconUsers, IconClipboardCheck } from "@tabler/icons-react";
import { UsersManager } from "./UsersManager";
import { FormAssignment } from "./FormAssignment";

export function UsersPageClient() {
  return (
    <Container size="xl" py="xl">
      <Tabs defaultValue="users" variant="outline">
        <Tabs.List mb="xl">
          <Tabs.Tab value="users" leftSection={<IconUsers size={18} />}>
            Správa uživatelů
          </Tabs.Tab>
          <Tabs.Tab value="assignments" leftSection={<IconClipboardCheck size={18} />}>
            Přiřazení formulářů
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="users">
          <UsersManager />
        </Tabs.Panel>

        <Tabs.Panel value="assignments">
          <FormAssignment />
        </Tabs.Panel>
      </Tabs>
    </Container>
  );
}


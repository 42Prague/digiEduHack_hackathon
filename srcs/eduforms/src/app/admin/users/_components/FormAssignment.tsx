"use client";

import { useState } from "react";
import { api } from "~/trpc/react";
import {
  Button,
  Select,
  Paper,
  Group,
  Stack,
  Title,
  Text,
  Alert,
  Loader,
  Center,
  Card,
  Divider,
  Tabs,
  Badge,
  Checkbox,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconClipboardCheck,
  IconUser,
  IconSchool,
  IconCheck,
  IconFileText,
  IconUsers,
} from "@tabler/icons-react";
import { notifications } from "@mantine/notifications";

export function FormAssignment() {
  // State for individual user assignment
  const [selectedForm, setSelectedForm] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [selectedInstitution, setSelectedInstitution] = useState<string | null>(null);

  // State for institution assignment
  const [institutionForm, setInstitutionForm] = useState<string | null>(null);
  const [institutionTarget, setInstitutionTarget] = useState<string | null>(null);
  const [allowDuplicates, setAllowDuplicates] = useState(false);

  // Queries
  const { data: forms, isLoading: formsLoading } = api.forms.list.useQuery();
  const { data: institutions, isLoading: institutionsLoading } = api.institutions.list.useQuery();
  
  // Query users by institution (only when institution is selected)
  const {
    data: users,
    isLoading: usersLoading,
  } = api.admin.getUsersByInstitution.useQuery(
    { institutionId: selectedInstitution! },
    { enabled: !!selectedInstitution }
  );

  // Mutations
  const assignToUserMutation = api.forms.assignFormToUser.useMutation({
    onSuccess: () => {
      notifications.show({
        title: "Úspěch!",
        message: "Formulář byl úspěšně přiřazen uživateli",
        color: "green",
        icon: <IconCheck size={16} />,
      });
      setSelectedForm(null);
      setSelectedUser(null);
      setSelectedInstitution(null);
    },
    onError: (error) => {
      notifications.show({
        title: "Chyba",
        message: error.message || "Nepodařilo se přiřadit formulář",
        color: "red",
        icon: <IconAlertCircle size={16} />,
      });
    },
  });

  const assignToInstitutionMutation = api.forms.assignFormToInstitution.useMutation({
    onSuccess: (result) => {
      notifications.show({
        title: "Úspěch!",
        message: result.message,
        color: "green",
        icon: <IconCheck size={16} />,
      });
      setInstitutionForm(null);
      setInstitutionTarget(null);
    },
    onError: (error) => {
      notifications.show({
        title: "Chyba",
        message: error.message || "Nepodařilo se přiřadit formulář instituci",
        color: "red",
        icon: <IconAlertCircle size={16} />,
      });
    },
  });

  const handleAssignToUser = () => {
    if (!selectedForm || !selectedUser) {
      notifications.show({
        title: "Chyba",
        message: "Vyberte prosím formulář a uživatele",
        color: "red",
        icon: <IconAlertCircle size={16} />,
      });
      return;
    }

    assignToUserMutation.mutate({
      formId: selectedForm,
      userId: selectedUser,
    });
  };

  const handleAssignToInstitution = () => {
    if (!institutionForm || !institutionTarget) {
      notifications.show({
        title: "Chyba",
        message: "Vyberte prosím formulář a instituci",
        color: "red",
        icon: <IconAlertCircle size={16} />,
      });
      return;
    }

    assignToInstitutionMutation.mutate({
      formId: institutionForm,
      institutionId: institutionTarget,
      allowDuplicates: allowDuplicates,
    });
  };

  if (formsLoading || institutionsLoading) {
    return (
      <Center h={300}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Načítání...</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="xl">
      {/* Header */}
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={1}>Přiřazení formulářů</Title>
          <Text c="dimmed" mt="xs">
            Přiřaďte formuláře jednotlivým uživatelům nebo celým institucím
          </Text>
        </div>
      </Group>

      <Tabs defaultValue="user" variant="pills">
        <Tabs.List mb="xl">
          <Tabs.Tab value="user" leftSection={<IconUser size={16} />}>
            Přiřadit uživateli
          </Tabs.Tab>
          <Tabs.Tab value="institution" leftSection={<IconSchool size={16} />}>
            Přiřadit instituci
          </Tabs.Tab>
        </Tabs.List>

        {/* ASSIGN TO USER TAB */}
        <Tabs.Panel value="user">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconUser size={24} style={{ color: "var(--mantine-color-blue-6)" }} />
              <Title order={3}>Přiřadit formulář uživateli</Title>
            </Group>
            
            <Text size="sm" c="dimmed" mb="lg">
              Vyberte formulář a uživatele, kterému chcete formulář přiřadit. Uživatel bude moci formulář vyplnit ve svém dashboardu.
            </Text>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAssignToUser();
              }}
            >
              <Stack gap="md">
                {/* Form Selection */}
                <Select
                  label="Formulář"
                  placeholder="Vyberte formulář..."
                  description="Formulář, který chcete přiřadit"
                  data={
                    forms?.map((form) => ({
                      value: form.id,
                      label: form.label,
                    })) ?? []
                  }
                  value={selectedForm}
                  onChange={setSelectedForm}
                  searchable
                  leftSection={<IconFileText size={16} />}
                  required
                  withAsterisk
                />

                <Divider label="Výběr uživatele" labelPosition="center" />

                {/* Institution Selection for User */}
                <Select
                  label="Instituce"
                  placeholder="Nejprve vyberte instituci..."
                  description="Vyberte instituci pro zobrazení jejích uživatelů"
                  data={
                    institutions?.map((inst) => ({
                      value: inst.id,
                      label: inst.label,
                    })) ?? []
                  }
                  value={selectedInstitution}
                  onChange={(value) => {
                    setSelectedInstitution(value);
                    setSelectedUser(null); // Reset user selection when institution changes
                  }}
                  searchable
                  leftSection={<IconSchool size={16} />}
                  clearable
                />

                {/* User Selection */}
                {selectedInstitution && (
                  <>
                    {usersLoading ? (
                      <Center h={100}>
                        <Loader size="sm" />
                      </Center>
                    ) : (
                      <Select
                        label="Uživatel"
                        placeholder="Vyberte uživatele..."
                        description="Uživatel, kterému bude formulář přiřazen"
                        data={
                          users?.map((user) => ({
                            value: user.id,
                            label: `${user.name} (${user.email})`,
                          })) ?? []
                        }
                        value={selectedUser}
                        onChange={setSelectedUser}
                        searchable
                        leftSection={<IconUser size={16} />}
                        required
                        withAsterisk
                        disabled={!users || users.length === 0}
                        rightSection={
                          users && users.length > 0 ? (
                            <Badge size="sm" variant="light">
                              {users.length}
                            </Badge>
                          ) : null
                        }
                      />
                    )}
                  </>
                )}

                {selectedInstitution && users && users.length === 0 && (
                  <Alert
                    icon={<IconAlertCircle size={16} />}
                    title="Žádní uživatelé"
                    color="yellow"
                    variant="light"
                  >
                    Vybraná instituce nemá žádné uživatele. Nejprve vytvořte uživatele pro tuto instituci.
                  </Alert>
                )}

                {assignToUserMutation.error && (
                  <Alert
                    icon={<IconAlertCircle size={16} />}
                    title="Chyba"
                    color="red"
                    variant="light"
                  >
                    {assignToUserMutation.error.message}
                  </Alert>
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    type="submit"
                    leftSection={<IconClipboardCheck size={16} />}
                    loading={assignToUserMutation.isPending}
                    disabled={!selectedForm || !selectedUser}
                  >
                    Přiřadit formulář
                  </Button>
                </Group>
              </Stack>
            </form>
          </Card>
        </Tabs.Panel>

        {/* ASSIGN TO INSTITUTION TAB */}
        <Tabs.Panel value="institution">
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconSchool size={24} style={{ color: "var(--mantine-color-green-6)" }} />
              <Title order={3}>Přiřadit formulář celé instituci</Title>
            </Group>
            
            <Text size="sm" c="dimmed" mb="lg">
              Vyberte formulář a instituci. Formulář bude automaticky přiřazen všem uživatelům v této instituci.
            </Text>

            <Alert
              icon={<IconUsers size={16} />}
              title="Hromadné přiřazení"
              color="blue"
              variant="light"
              mb="lg"
            >
              Tato akce přiřadí formulář všem současným uživatelům v instituci. Uživatelé, kteří již mají formulář přiřazen, budou přeskočeni.
            </Alert>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAssignToInstitution();
              }}
            >
              <Stack gap="md">
                {/* Form Selection */}
                <Select
                  label="Formulář"
                  placeholder="Vyberte formulář..."
                  description="Formulář, který chcete přiřadit všem uživatelům instituce"
                  data={
                    forms?.map((form) => ({
                      value: form.id,
                      label: form.label,
                    })) ?? []
                  }
                  value={institutionForm}
                  onChange={setInstitutionForm}
                  searchable
                  leftSection={<IconFileText size={16} />}
                  required
                  withAsterisk
                />

                {/* Institution Selection */}
                <Select
                  label="Instituce"
                  placeholder="Vyberte instituci..."
                  description="Všichni uživatelé této instituce dostanou formulář"
                  data={
                    institutions?.map((inst) => ({
                      value: inst.id,
                      label: inst.label,
                    })) ?? []
                  }
                  value={institutionTarget}
                  onChange={setInstitutionTarget}
                  searchable
                  leftSection={<IconSchool size={16} />}
                  required
                  withAsterisk
                />

                {/* Allow Duplicates Option */}
                <Checkbox
                  label="Povolit vícenásobné přiřazení"
                  description="Umožní přiřadit formulář i uživatelům, kteří jej již mají přiřazen (vytvoří novou instanci)"
                  checked={allowDuplicates}
                  onChange={(event) => setAllowDuplicates(event.currentTarget.checked)}
                />

                {assignToInstitutionMutation.error && (
                  <Alert
                    icon={<IconAlertCircle size={16} />}
                    title="Chyba"
                    color="red"
                    variant="light"
                  >
                    {assignToInstitutionMutation.error.message}
                  </Alert>
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    type="submit"
                    leftSection={<IconClipboardCheck size={16} />}
                    loading={assignToInstitutionMutation.isPending}
                    disabled={!institutionForm || !institutionTarget}
                    color="green"
                  >
                    Přiřadit celé instituci
                  </Button>
                </Group>
              </Stack>
            </form>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}


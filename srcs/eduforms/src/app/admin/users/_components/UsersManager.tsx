"use client";

import { useState } from "react";
import { api } from "~/trpc/react";
import {
  Button,
  TextInput,
  Table,
  Paper,
  Group,
  Stack,
  Title,
  Text,
  Modal,
  Alert,
  ActionIcon,
  Loader,
  Center,
  Badge,
  Select,
  PasswordInput,
  Card,
  Divider,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconPlus,
  IconPencil,
  IconTrash,
  IconAlertCircle,
  IconUserPlus,
  IconSchool,
  IconUsers,
  IconMail,
  IconShieldCheck,
} from "@tabler/icons-react";

export function UsersManager() {
  const [opened, { open, close }] = useDisclosure(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selectedInstitution, setSelectedInstitution] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "user",
  });

  // Queries
  const { data: institutions, isLoading: institutionsLoading } = api.institutions.list.useQuery();
  
  const {
    data: users,
    isLoading: usersLoading,
    refetch,
  } = api.admin.getUsersByInstitution.useQuery(
    { institutionId: selectedInstitution! },
    { enabled: !!selectedInstitution }
  );

  // Mutations
  const createMutation = api.admin.createUser.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      setFormData({ name: "", email: "", password: "", role: "user" });
    },
  });

  const updateMutation = api.admin.updateUser.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      setEditingId(null);
      setFormData({ name: "", email: "", password: "", role: "user" });
    },
  });

  const deleteMutation = api.admin.deleteUser.useMutation({
    onSuccess: () => {
      void refetch();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstitution) return;

    if (editingId) {
      updateMutation.mutate({
        userId: editingId,
        name: formData.name,
        email: formData.email,
        role: formData.role,
        institutionId: selectedInstitution,
      });
    } else {
      createMutation.mutate({
        ...formData,
        institutionId: selectedInstitution,
      });
    }
  };

  const handleEdit = (user: {
    id: string;
    name: string;
    email: string;
    role: string | null;
  }) => {
    setEditingId(user.id);
    setFormData({
      name: user.name,
      email: user.email,
      password: "",
      role: user.role ?? "user",
    });
    open();
  };

  const handleDelete = (id: string) => {
    if (confirm("Opravdu chcete smazat tohoto uživatele?")) {
      deleteMutation.mutate({ userId: id });
    }
  };

  const handleOpenCreate = () => {
    if (!selectedInstitution) {
      alert("Nejprve prosím vyberte instituci");
      return;
    }
    setEditingId(null);
    setFormData({ name: "", email: "", password: "", role: "user" });
    open();
  };

  const handleClose = () => {
    close();
    setEditingId(null);
    setFormData({ name: "", email: "", password: "", role: "user" });
  };

  const selectedInstitutionData = institutions?.find(
    (inst) => inst.id === selectedInstitution
  );

  if (institutionsLoading) {
    return (
      <Center h={400}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Načítání institucí...</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="xl">
      {/* Header */}
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={1}>Správa uživatelů</Title>
          <Text c="dimmed" mt="xs">
            Vytváření a správa uživatelských účtů pro instituce
          </Text>
        </div>
      </Group>

      {/* Institution Selection Card */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group mb="md">
          <IconSchool size={24} style={{ color: "var(--mantine-color-blue-6)" }} />
          <Title order={3}>Výběr instituce</Title>
        </Group>
        <Text size="sm" c="dimmed" mb="md">
          Vyberte instituci pro zobrazení a správu jejích uživatelů
        </Text>
        <Select
          placeholder="Vyberte instituci..."
          data={
            institutions?.map((inst) => ({
              value: inst.id,
              label: inst.label,
            })) ?? []
          }
          value={selectedInstitution}
          onChange={(value) => setSelectedInstitution(value)}
          size="md"
          searchable
          leftSection={<IconSchool size={16} />}
          clearable
        />
      </Card>

      {/* Create User Button - Only shown when institution is selected */}
      {selectedInstitution && (
        <Group justify="flex-end">
          <Button
            leftSection={<IconUserPlus size={16} />}
            onClick={handleOpenCreate}
            size="md"
          >
            Přidat nového uživatele
          </Button>
        </Group>
      )}

      {/* Modal for Create/Edit */}
      <Modal
        opened={opened}
        onClose={handleClose}
        title={
          <Group gap="sm">
            <IconUserPlus size={20} />
            <Title order={3}>{editingId ? "Upravit uživatele" : "Vytvořit nového uživatele"}</Title>
          </Group>
        }
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {selectedInstitutionData && (
              <Alert
                icon={<IconSchool size={16} />}
                title="Instituce"
                color="blue"
                variant="light"
              >
                {selectedInstitutionData.label}
              </Alert>
            )}

            <TextInput
              label="Celé jméno"
              placeholder="např. Jan Novák"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.currentTarget.value })}
              required
              withAsterisk
              leftSection={<IconUsers size={16} />}
            />

            <TextInput
              label="E-mailová adresa"
              placeholder="např. jan.novak@example.com"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.currentTarget.value })}
              required
              withAsterisk
              leftSection={<IconMail size={16} />}
            />

            {!editingId && (
              <PasswordInput
                label="Heslo"
                placeholder="Zadejte heslo"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.currentTarget.value })}
                description="Minimálně 8 znaků"
                required
                withAsterisk
              />
            )}

            <Select
              label="Role"
              placeholder="Vyberte roli"
              data={[
                { value: "user", label: "Uživatel" },
                { value: "teacher", label: "Učitel" },
                { value: "admin", label: "Administrátor" },
              ]}
              value={formData.role}
              onChange={(value) => setFormData({ ...formData, role: value ?? "user" })}
              required
              withAsterisk
              leftSection={<IconShieldCheck size={16} />}
            />

            {(createMutation.error || updateMutation.error) && (
              <Alert
                icon={<IconAlertCircle size={16} />}
                title="Chyba"
                color="red"
                variant="light"
              >
                {createMutation.error?.message || updateMutation.error?.message}
              </Alert>
            )}

            <Divider />

            <Group justify="flex-end" mt="md">
              <Button variant="subtle" onClick={handleClose}>
                Zrušit
              </Button>
              <Button
                type="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingId ? "Aktualizovat uživatele" : "Vytvořit uživatele"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Users List */}
      {selectedInstitution ? (
        <Paper shadow="sm" p="xl" radius="md">
          <Group justify="space-between" mb="lg">
            <Group>
              <IconUsers size={24} style={{ color: "var(--mantine-color-blue-6)" }} />
              <Title order={2}>Uživatelé</Title>
            </Group>
            <Badge size="lg" variant="light">
              {users?.length ?? 0} {users?.length === 1 ? "uživatel" : users?.length < 5 ? "uživatelé" : "uživatelů"}
            </Badge>
          </Group>

          {usersLoading ? (
            <Center h={200}>
              <Stack align="center" gap="md">
                <Loader size="lg" />
                <Text c="dimmed">Načítání uživatelů...</Text>
              </Stack>
            </Center>
          ) : !users || users.length === 0 ? (
            <Center h={200}>
              <Stack align="center" gap="xs">
                <IconUsers size={48} style={{ opacity: 0.3 }} />
                <Text c="dimmed" size="lg">
                  Nebyli nalezeni žádní uživatelé
                </Text>
                <Text c="dimmed" size="sm">
                  Vytvořte prvního uživatele pro tuto instituci
                </Text>
              </Stack>
            </Center>
          ) : (
            <Table.ScrollContainer minWidth={500}>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Jméno</Table.Th>
                    <Table.Th>E-mail</Table.Th>
                    <Table.Th>Role</Table.Th>
                    <Table.Th>Stav</Table.Th>
                    <Table.Th>Vytvořeno</Table.Th>
                    <Table.Th style={{ textAlign: "right" }}>Akce</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {users.map((user) => (
                    <Table.Tr key={user.id}>
                      <Table.Td fw={500}>{user.name}</Table.Td>
                      <Table.Td c="dimmed">{user.email}</Table.Td>
                      <Table.Td>
                        <Badge
                          color={
                            user.role === "admin"
                              ? "red"
                              : user.role === "teacher"
                              ? "blue"
                              : "gray"
                          }
                          variant="light"
                        >
                          {user.role ?? "user"}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        {user.banned ? (
                          <Badge color="red" variant="filled">
                            Blokován
                          </Badge>
                        ) : user.emailVerified ? (
                          <Badge color="green" variant="light">
                            Ověřen
                          </Badge>
                        ) : (
                          <Badge color="yellow" variant="light">
                            Neověřen
                          </Badge>
                        )}
                      </Table.Td>
                      <Table.Td c="dimmed">
                        {new Date(user.createdAt).toLocaleDateString("cs-CZ")}
                      </Table.Td>
                      <Table.Td>
                        <Group justify="flex-end" gap="xs">
                          <ActionIcon
                            variant="subtle"
                            color="blue"
                            onClick={() => handleEdit(user)}
                            title="Upravit"
                          >
                            <IconPencil size={18} />
                          </ActionIcon>
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            onClick={() => handleDelete(user.id)}
                            loading={deleteMutation.isPending}
                            title="Smazat"
                          >
                            <IconTrash size={18} />
                          </ActionIcon>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          )}
        </Paper>
      ) : (
        <Paper shadow="sm" p="xl" radius="md">
          <Center h={300}>
            <Stack align="center" gap="md">
              <IconSchool size={64} style={{ opacity: 0.3 }} />
              <Title order={3} c="dimmed">
                Vyberte instituci
              </Title>
              <Text c="dimmed" size="sm" ta="center" maw={400}>
                Vyberte prosím instituci z rozbalovací nabídky výše pro zobrazení a správu jejích uživatelů
              </Text>
            </Stack>
          </Center>
        </Paper>
      )}
    </Stack>
  );
}


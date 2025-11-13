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
    if (confirm("Are you sure you want to delete this user?")) {
      deleteMutation.mutate({ userId: id });
    }
  };

  const handleOpenCreate = () => {
    if (!selectedInstitution) {
      alert("Please select an institution first");
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
          <Text c="dimmed">Loading institutions...</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="xl">
      {/* Header */}
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={1}>User Management</Title>
          <Text c="dimmed" mt="xs">
            Create and manage user accounts for institutions
          </Text>
        </div>
      </Group>

      {/* Institution Selection Card */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group mb="md">
          <IconSchool size={24} style={{ color: "var(--mantine-color-blue-6)" }} />
          <Title order={3}>Select Institution</Title>
        </Group>
        <Text size="sm" c="dimmed" mb="md">
          Choose an institution to view and manage its users
        </Text>
        <Select
          placeholder="Select an institution..."
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
            Add New User
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
            <Title order={3}>{editingId ? "Edit User" : "Create New User"}</Title>
          </Group>
        }
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {selectedInstitutionData && (
              <Alert
                icon={<IconSchool size={16} />}
                title="Institution"
                color="blue"
                variant="light"
              >
                {selectedInstitutionData.label}
              </Alert>
            )}

            <TextInput
              label="Full Name"
              placeholder="e.g., Jan Novák"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.currentTarget.value })}
              required
              withAsterisk
              leftSection={<IconUsers size={16} />}
            />

            <TextInput
              label="Email Address"
              placeholder="e.g., jan.novak@example.com"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.currentTarget.value })}
              required
              withAsterisk
              leftSection={<IconMail size={16} />}
            />

            {!editingId && (
              <PasswordInput
                label="Password"
                placeholder="Enter password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.currentTarget.value })}
                description="Minimum 8 characters"
                required
                withAsterisk
              />
            )}

            <Select
              label="Role"
              placeholder="Select role"
              data={[
                { value: "user", label: "User" },
                { value: "teacher", label: "Teacher" },
                { value: "admin", label: "Admin" },
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
                title="Error"
                color="red"
                variant="light"
              >
                {createMutation.error?.message || updateMutation.error?.message}
              </Alert>
            )}

            <Divider />

            <Group justify="flex-end" mt="md">
              <Button variant="subtle" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingId ? "Update User" : "Create User"}
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
              <Title order={2}>Users</Title>
            </Group>
            <Badge size="lg" variant="light">
              {users?.length ?? 0} {users?.length === 1 ? "user" : "users"}
            </Badge>
          </Group>

          {usersLoading ? (
            <Center h={200}>
              <Stack align="center" gap="md">
                <Loader size="lg" />
                <Text c="dimmed">Loading users...</Text>
              </Stack>
            </Center>
          ) : !users || users.length === 0 ? (
            <Center h={200}>
              <Stack align="center" gap="xs">
                <IconUsers size={48} style={{ opacity: 0.3 }} />
                <Text c="dimmed" size="lg">
                  No users found
                </Text>
                <Text c="dimmed" size="sm">
                  Create your first user for this institution
                </Text>
              </Stack>
            </Center>
          ) : (
            <Table.ScrollContainer minWidth={500}>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Email</Table.Th>
                    <Table.Th>Role</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Created</Table.Th>
                    <Table.Th style={{ textAlign: "right" }}>Actions</Table.Th>
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
                            Banned
                          </Badge>
                        ) : user.emailVerified ? (
                          <Badge color="green" variant="light">
                            Verified
                          </Badge>
                        ) : (
                          <Badge color="yellow" variant="light">
                            Unverified
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
                            title="Edit"
                          >
                            <IconPencil size={18} />
                          </ActionIcon>
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            onClick={() => handleDelete(user.id)}
                            loading={deleteMutation.isPending}
                            title="Delete"
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
                Select an Institution
              </Title>
              <Text c="dimmed" size="sm" ta="center" maw={400}>
                Please select an institution from the dropdown above to view and manage its users
              </Text>
            </Stack>
          </Center>
        </Paper>
      )}
    </Stack>
  );
}


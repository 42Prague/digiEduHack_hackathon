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
  Textarea,
  Card,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconPlus,
  IconPencil,
  IconTrash,
  IconAlertCircle,
  IconEdit,
  IconForms,
} from "@tabler/icons-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function FormsManager() {
  const router = useRouter();
  const [opened, { open, close }] = useDisclosure(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    label: "",
    description: "",
  });

  // Queries
  const { data: forms, isLoading, refetch } = api.forms.list.useQuery();

  // Mutations
  const createMutation = api.forms.create.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      resetForm();
    },
  });

  const updateMutation = api.forms.update.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      resetForm();
    },
  });

  const deleteMutation = api.forms.delete.useMutation({
    onSuccess: () => {
      void refetch();
    },
  });

  const resetForm = () => {
    setFormData({ label: "", description: "" });
    setEditingId(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      updateMutation.mutate({ id: editingId, ...formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (form: any) => {
    setEditingId(form.id);
    setFormData({
      label: form.label,
      description: form.description || "",
    });
    open();
  };

  const handleDelete = (id: string) => {
    if (confirm("Opravdu chcete smazat tento formulář?")) {
      deleteMutation.mutate({ id });
    }
  };

  const handleOpenCreate = () => {
    resetForm();
    open();
  };

  if (isLoading) {
    return (
      <Center h={400}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Načítání formulářů...</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <div>
          <Title order={1}>Správa formulářů</Title>
          <Text c="dimmed" size="sm">
            Vytváření a správa formulářů s opakovaně použitelnými poli
          </Text>
        </div>
        <Group>
          <Button
            component={Link}
            href="/admin/forms/fields"
            variant="light"
            leftSection={<IconForms size={16} />}
          >
            Spravovat pole
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={handleOpenCreate}>
            Vytvořit formulář
          </Button>
        </Group>
      </Group>

      {createMutation.error && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="Chyba"
          color="red"
          onClose={() => createMutation.reset()}
          withCloseButton
        >
          {createMutation.error.message}
        </Alert>
      )}

      {forms && forms.length === 0 ? (
        <Card withBorder p="xl">
          <Stack align="center" gap="md">
            <IconForms size={48} stroke={1.5} opacity={0.5} />
            <Text size="lg" fw={500}>
              Zatím žádné formuláře
            </Text>
            <Text c="dimmed" ta="center">
              Vytvořte svůj první formulář pro začátek. Můžete do něj přidat pole
              z knihovny polí.
            </Text>
            <Button onClick={handleOpenCreate} leftSection={<IconPlus size={16} />}>
              Vytvořit první formulář
            </Button>
          </Stack>
        </Card>
      ) : (
        <Paper shadow="sm" p="md" withBorder>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Název formuláře</Table.Th>
                <Table.Th>Popis</Table.Th>
                <Table.Th>Vytvořeno</Table.Th>
                <Table.Th>Naposledy aktualizováno</Table.Th>
                <Table.Th>Akce</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {forms?.map((form) => (
                <Table.Tr key={form.id}>
                  <Table.Td>
                    <Text fw={500}>{form.label}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {form.description || "-"}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {new Date(form.createdAt).toLocaleDateString()}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {new Date(form.updatedAt).toLocaleDateString()}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <ActionIcon
                        variant="subtle"
                        color="blue"
                        onClick={() => router.push(`/admin/forms/${form.id}`)}
                        title="Upravit návrháře formuláře"
                      >
                        <IconEdit size={16} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="gray"
                        onClick={() => handleEdit(form)}
                        title="Upravit detaily"
                      >
                        <IconPencil size={16} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        onClick={() => handleDelete(form.id)}
                        title="Smazat"
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Paper>
      )}

      <Modal
        opened={opened}
        onClose={() => {
          close();
          resetForm();
        }}
        title={
          <Title order={3}>{editingId ? "Upravit formulář" : "Vytvořit formulář"}</Title>
        }
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <TextInput
              label="Název formuláře"
              placeholder="např. Dotazník pro učitele 2024"
              value={formData.label}
              onChange={(e) =>
                setFormData({ ...formData, label: e.target.value })
              }
              required
            />

            <Textarea
              label="Popis"
              placeholder="Popište účel tohoto formuláře"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              rows={4}
            />

            <Group justify="flex-end" mt="md">
              <Button
                variant="subtle"
                onClick={() => {
                  close();
                  resetForm();
                }}
              >
                Zrušit
              </Button>
              <Button
                type="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingId ? "Aktualizovat" : "Vytvořit"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}


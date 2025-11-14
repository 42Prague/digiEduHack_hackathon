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
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconPlus, IconPencil, IconTrash, IconAlertCircle } from "@tabler/icons-react";

export function InstitutionsManager() {
  const [opened, { open, close }] = useDisclosure(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ label: "", ico: "" });

  // Queries
  const { data: institutions, isLoading, refetch } = api.institutions.list.useQuery();

  // Mutations
  const createMutation = api.institutions.create.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      setFormData({ label: "", ico: "" });
    },
  });

  const updateMutation = api.institutions.update.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      setEditingId(null);
      setFormData({ label: "", ico: "" });
    },
  });

  const deleteMutation = api.institutions.delete.useMutation({
    onSuccess: () => {
      void refetch();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      updateMutation.mutate({ id: editingId, ...formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (inst: { id: string; label: string; ico: string }) => {
    setEditingId(inst.id);
    setFormData({ label: inst.label, ico: inst.ico });
    open();
  };

  const handleDelete = (id: string) => {
    if (confirm("Opravdu chcete smazat tuto instituci?")) {
      deleteMutation.mutate({ id });
    }
  };

  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData({ label: "", ico: "" });
    open();
  };

  const handleClose = () => {
    close();
    setEditingId(null);
    setFormData({ label: "", ico: "" });
  };

  if (isLoading) {
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
          <Title order={1}>Správa institucí</Title>
          <Text c="dimmed" mt="xs">
            Správa vzdělávacích institucí (škol) v České republice
          </Text>
        </div>
        <Button leftSection={<IconPlus size={16} />} onClick={handleOpenCreate}>
          Vytvořit novou instituci
        </Button>
      </Group>

      {/* Modal for Create/Edit */}
      <Modal
        opened={opened}
        onClose={handleClose}
        title={<Title order={3}>{editingId ? "Upravit instituci" : "Vytvořit novou instituci"}</Title>}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <TextInput
              label="Název instituce"
              placeholder="např. Základní škola Praha 1"
              value={formData.label}
              onChange={(e) => setFormData({ ...formData, label: e.currentTarget.value })}
              required
              withAsterisk
            />
            
            <TextInput
              label="IČO"
              placeholder="např. 12345678"
              value={formData.ico}
              onChange={(e) => setFormData({ ...formData, ico: e.currentTarget.value })}
              description="Identifikační číslo organizace"
              required
              withAsterisk
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

            <Group justify="flex-end" mt="md">
              <Button variant="subtle" onClick={handleClose}>
                Zrušit
              </Button>
              <Button
                type="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingId ? "Aktualizovat instituci" : "Vytvořit instituci"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Institutions List */}
      <Paper shadow="sm" p="xl" radius="md">
        <Group justify="space-between" mb="lg">
          <Title order={2}>Všechny instituce</Title>
          <Badge size="lg" variant="light">
            {institutions?.length ?? 0} celkem
          </Badge>
        </Group>

        {!institutions || institutions.length === 0 ? (
          <Center h={200}>
            <Stack align="center" gap="xs">
              <Text c="dimmed" size="lg">
                Nebyly nalezeny žádné instituce
              </Text>
              <Text c="dimmed" size="sm">
                Vytvořte první instituci pro začátek
              </Text>
            </Stack>
          </Center>
        ) : (
          <Table.ScrollContainer minWidth={500}>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Název</Table.Th>
                  <Table.Th>IČO</Table.Th>
                  <Table.Th>Vytvořeno</Table.Th>
                  <Table.Th style={{ textAlign: "right" }}>Akce</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {institutions.map((inst) => (
                  <Table.Tr key={inst.id}>
                    <Table.Td fw={500}>{inst.label}</Table.Td>
                    <Table.Td c="dimmed">{inst.ico}</Table.Td>
                    <Table.Td c="dimmed">
                      {new Date(inst.createdAt).toLocaleDateString("cs-CZ")}
                    </Table.Td>
                    <Table.Td>
                      <Group justify="flex-end" gap="xs">
                        <ActionIcon
                          variant="subtle"
                          color="blue"
                          onClick={() => handleEdit(inst)}
                          title="Upravit"
                        >
                          <IconPencil size={18} />
                        </ActionIcon>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => handleDelete(inst.id)}
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
    </Stack>
  );
}


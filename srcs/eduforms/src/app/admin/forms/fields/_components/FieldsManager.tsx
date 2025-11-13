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
  NumberInput,
  Textarea,
  Checkbox,
  Divider,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconPlus,
  IconPencil,
  IconTrash,
  IconAlertCircle,
  IconArrowLeft,
} from "@tabler/icons-react";
import Link from "next/link";
import type { FieldConfigType } from "~/server/db/schema";

type FieldType = FieldConfigType["type"];

export function FieldsManager() {
  const [opened, { open, close }] = useDisclosure(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    type: "text" as FieldType,
  });
  const [config, setConfig] = useState<Partial<FieldConfigType>>({
    label: "",
    required: false,
    help: "",
  });

  // Queries
  const { data: fields, isLoading, refetch } = api.forms.listFields.useQuery();

  // Mutations
  const createMutation = api.forms.createField.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      resetForm();
    },
  });

  const updateMutation = api.forms.updateField.useMutation({
    onSuccess: () => {
      void refetch();
      close();
      resetForm();
    },
  });

  const deleteMutation = api.forms.deleteField.useMutation({
    onSuccess: () => {
      void refetch();
    },
  });

  const resetForm = () => {
    setFormData({ name: "", description: "", type: "text" });
    setConfig({ label: "", required: false, help: "" });
    setEditingId(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const fieldConfig = { ...config, type: formData.type } as FieldConfigType;

    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        name: formData.name,
        description: formData.description,
        config: fieldConfig,
      });
    } else {
      createMutation.mutate({
        name: formData.name,
        description: formData.description,
        config: fieldConfig,
      });
    }
  };

  const handleEdit = (field: any) => {
    setEditingId(field.id);
    setFormData({
      name: field.name,
      description: field.description || "",
      type: field.config.type,
    });
    setConfig(field.config);
    open();
  };

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this field?")) {
      deleteMutation.mutate({ id });
    }
  };

  const handleOpenCreate = () => {
    resetForm();
    open();
  };

  const renderFieldTypeConfig = () => {
    switch (formData.type) {
      case "text":
      case "textarea":
        return (
          <>
            <TextInput
              label="Placeholder"
              value={(config as any).placeholder || ""}
              onChange={(e) =>
                setConfig({ ...config, placeholder: e.target.value })
              }
            />
            {formData.type === "textarea" && (
              <NumberInput
                label="Rows"
                value={(config as any).rows || 3}
                onChange={(val) => setConfig({ ...config, rows: val as number })}
                min={1}
                max={20}
              />
            )}
          </>
        );

      case "number":
        return (
          <>
            <NumberInput
              label="Min Value"
              value={(config as any).minValue}
              onChange={(val) =>
                setConfig({ ...config, minValue: val as number })
              }
            />
            <NumberInput
              label="Max Value"
              value={(config as any).maxValue}
              onChange={(val) =>
                setConfig({ ...config, maxValue: val as number })
              }
            />
            <NumberInput
              label="Default Value"
              value={(config as any).defaultValue}
              onChange={(val) =>
                setConfig({ ...config, defaultValue: val as number })
              }
            />
          </>
        );

      case "date":
        return (
          <TextInput
            label="Default Value (ISO Date)"
            value={(config as any).defaultValue || ""}
            onChange={(e) =>
              setConfig({ ...config, defaultValue: e.target.value })
            }
            placeholder="2024-01-01"
          />
        );

      case "boolean":
        return (
          <Checkbox
            label="Default Checked"
            checked={(config as any).defaultValue || false}
            onChange={(e) =>
              setConfig({ ...config, defaultValue: e.target.checked })
            }
          />
        );

      case "select":
      case "radio":
      case "multiselect":
        return (
          <>
            <Textarea
              label="Options (one per line)"
              value={(config as any).options?.join("\n") || ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  options: e.target.value.split("\n").filter((o) => o.trim()),
                })
              }
              rows={5}
              required
            />
            {formData.type === "multiselect" && (
              <NumberInput
                label="Max Selections"
                value={(config as any).maxSelections}
                onChange={(val) =>
                  setConfig({ ...config, maxSelections: val as number })
                }
                min={1}
              />
            )}
          </>
        );

      case "slider":
        return (
          <>
            <Textarea
              label="Options (comma separated numbers)"
              value={(config as any).options?.join(", ") || ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  options: e.target.value
                    .split(",")
                    .map((v) => parseInt(v.trim()))
                    .filter((n) => !isNaN(n)),
                })
              }
              placeholder="1, 2, 3, 4, 5"
              required
            />
            <NumberInput
              label="Default Value"
              value={(config as any).defaultValue}
              onChange={(val) =>
                setConfig({ ...config, defaultValue: val as number })
              }
            />
          </>
        );

      case "discrete_range":
        return (
          <Textarea
            label="Options (format: value:label, one per line)"
            value={
              (config as any).options
                ?.map((o: any) => `${o.value}:${o.label}`)
                .join("\n") || ""
            }
            onChange={(e) => {
              const options = e.target.value
                .split("\n")
                .filter((line) => line.trim())
                .map((line) => {
                  const [value, label] = line.split(":");
                  return {
                    value: parseInt(value?.trim() || "0"),
                    label: label?.trim() || "",
                  };
                })
                .filter((o) => !isNaN(o.value) && o.label);
              setConfig({ ...config, options });
            }}
            rows={5}
            placeholder="1:Very Low&#10;2:Low&#10;3:Medium&#10;4:High&#10;5:Very High"
            required
          />
        );

      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <Center h={400}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Loading fields...</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <div>
          <Group>
            <ActionIcon
              component={Link}
              href="/admin/forms"
              variant="subtle"
              size="lg"
            >
              <IconArrowLeft size={20} />
            </ActionIcon>
            <Title order={1}>Field Library</Title>
          </Group>
          <Text c="dimmed" size="sm">
            Create reusable fields that can be used across multiple forms
          </Text>
        </div>
        <Button leftSection={<IconPlus size={16} />} onClick={handleOpenCreate}>
          Create Field
        </Button>
      </Group>

      {createMutation.error && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="Error"
          color="red"
          onClose={() => createMutation.reset()}
          withCloseButton
        >
          {createMutation.error.message}
        </Alert>
      )}

      <Paper shadow="sm" p="md" withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Label</Table.Th>
              <Table.Th>Required</Table.Th>
              <Table.Th>Description</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {fields?.map((field) => (
              <Table.Tr key={field.id}>
                <Table.Td>
                  <Text fw={500}>{field.name}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light">{field.config.type}</Badge>
                </Table.Td>
                <Table.Td>{field.config.label}</Table.Td>
                <Table.Td>
                  {field.config.required ? (
                    <Badge color="red" size="sm">
                      Required
                    </Badge>
                  ) : (
                    <Badge color="gray" size="sm">
                      Optional
                    </Badge>
                  )}
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed" lineClamp={1}>
                    {field.description || "-"}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <ActionIcon
                      variant="subtle"
                      color="blue"
                      onClick={() => handleEdit(field)}
                    >
                      <IconPencil size={16} />
                    </ActionIcon>
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      onClick={() => handleDelete(field.id)}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
            {fields?.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center" c="dimmed" py="xl">
                    No fields created yet. Create your first field!
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal
        opened={opened}
        onClose={() => {
          close();
          resetForm();
        }}
        title={
          <Title order={3}>{editingId ? "Edit Field" : "Create Field"}</Title>
        }
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <TextInput
              label="Field Name"
              placeholder="e.g., teacher_id, student_rating"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              required
            />

            <Textarea
              label="Description"
              placeholder="Describe the purpose of this field"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              rows={2}
            />

            <Divider label="Field Configuration" labelPosition="center" />

            <Select
              label="Field Type"
              value={formData.type}
              onChange={(value) =>
                setFormData({ ...formData, type: value as FieldType })
              }
              data={[
                { value: "text", label: "Text Input" },
                { value: "textarea", label: "Text Area" },
                { value: "number", label: "Number Input" },
                { value: "date", label: "Date Picker" },
                { value: "boolean", label: "Checkbox" },
                { value: "select", label: "Select Dropdown" },
                { value: "radio", label: "Radio Buttons" },
                { value: "multiselect", label: "Multi-Select" },
                { value: "slider", label: "Slider" },
                { value: "discrete_range", label: "Discrete Range" },
              ]}
              required
            />

            <TextInput
              label="Field Label"
              placeholder="Label shown to users"
              value={(config as any).label || ""}
              onChange={(e) =>
                setConfig({ ...config, label: e.target.value })
              }
              required
            />

            <Checkbox
              label="Required Field"
              checked={(config as any).required || false}
              onChange={(e) =>
                setConfig({ ...config, required: e.target.checked })
              }
            />

            <Textarea
              label="Help Text"
              placeholder="Additional guidance for users"
              value={(config as any).help || ""}
              onChange={(e) => setConfig({ ...config, help: e.target.value })}
              rows={2}
            />

            {renderFieldTypeConfig()}

            <Group justify="flex-end" mt="md">
              <Button
                variant="subtle"
                onClick={() => {
                  close();
                  resetForm();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingId ? "Update" : "Create"}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}


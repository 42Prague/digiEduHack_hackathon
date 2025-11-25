"use client";

import { useState } from "react";
import { api } from "~/trpc/react";
import {
  Button,
  Paper,
  Group,
  Stack,
  Title,
  Text,
  Loader,
  Center,
  Badge,
  ActionIcon,
  Grid,
  Card,
  ScrollArea,
  Divider,
  Alert,
  Tooltip,
} from "@mantine/core";
import {
  IconArrowLeft,
  IconPlus,
  IconTrash,
  IconGripVertical,
  IconAlertCircle,
} from "@tabler/icons-react";
import Link from "next/link";
import { FieldPreview } from "./FieldPreview";

interface FormBuilderProps {
  formId: string;
}

export function FormBuilder({ formId }: FormBuilderProps) {
  const [selectedFieldOrder, setSelectedFieldOrder] = useState<number | null>(
    null
  );

  // Queries
  const {
    data: formWithFields,
    isLoading: formLoading,
    refetch: refetchForm,
  } = api.forms.getWithFields.useQuery({ id: formId });

  const {
    data: availableFields,
    isLoading: fieldsLoading,
  } = api.forms.listFields.useQuery();

  // Mutations
  const addFieldMutation = api.forms.addFieldToForm.useMutation({
    onSuccess: () => {
      void refetchForm();
    },
  });

  const removeFieldMutation = api.forms.removeFieldFromForm.useMutation({
    onSuccess: () => {
      void refetchForm();
    },
  });

  const updateOrderMutation = api.forms.updateFieldOrder.useMutation({
    onSuccess: () => {
      void refetchForm();
    },
  });

  const handleAddField = (fieldId: string) => {
    const nextOrder = formWithFields?.fields?.length || 0;
    addFieldMutation.mutate({
      formId,
      fieldId,
      order: nextOrder,
    });
  };

  const handleRemoveField = (fieldId: string) => {
    if (confirm("Remove this field from the form?")) {
      removeFieldMutation.mutate({ formId, fieldId });
    }
  };

  const handleMoveUp = (fieldId: string, currentOrder: number) => {
    if (currentOrder > 0) {
      updateOrderMutation.mutate({
        formId,
        fieldId,
        order: currentOrder - 1,
      });
    }
  };

  const handleMoveDown = (fieldId: string, currentOrder: number) => {
    const maxOrder = (formWithFields?.fields?.length || 1) - 1;
    if (currentOrder < maxOrder) {
      updateOrderMutation.mutate({
        formId,
        fieldId,
        order: currentOrder + 1,
      });
    }
  };

  if (formLoading || fieldsLoading) {
    return (
      <Center h={400}>
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text c="dimmed">Loading form builder...</Text>
        </Stack>
      </Center>
    );
  }

  if (!formWithFields) {
    return (
      <Alert
        icon={<IconAlertCircle size={16} />}
        title="Form not found"
        color="red"
      >
        The requested form could not be found.
      </Alert>
    );
  }

  // Filter out fields already in the form
  const formFieldIds = new Set(formWithFields.fields?.map((f) => f.id) || []);
  const fieldsNotInForm =
    availableFields?.filter((f) => !formFieldIds.has(f.id)) || [];

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Group>
          <ActionIcon
            component={Link}
            href="/admin/forms"
            variant="subtle"
            size="lg"
          >
            <IconArrowLeft size={20} />
          </ActionIcon>
          <div>
            <Title order={1}>{formWithFields.label}</Title>
            <Text c="dimmed" size="sm">
              {formWithFields.description || "Build your form by adding fields"}
            </Text>
          </div>
        </Group>
        <Button
          component={Link}
          href="/admin/forms/fields"
          variant="light"
          leftSection={<IconPlus size={16} />}
        >
          Create New Field
        </Button>
      </Group>

      {addFieldMutation.error && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="Error"
          color="red"
          onClose={() => addFieldMutation.reset()}
          withCloseButton
        >
          {addFieldMutation.error.message}
        </Alert>
      )}

      <Grid>
        {/* Left Side - Form Preview */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Paper shadow="sm" p="md" withBorder>
            <Title order={3} mb="md">
              Form Preview
            </Title>

            {formWithFields.fields && formWithFields.fields.length > 0 ? (
              <Stack gap="md">
                {formWithFields.fields
                  .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                  .map((field, index) => (
                    <Card
                      key={field.id}
                      withBorder
                      p="md"
                      style={{
                        backgroundColor:
                          selectedFieldOrder === field.order
                            ? "var(--mantine-color-blue-0)"
                            : undefined,
                      }}
                    >
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <Group gap="xs">
                            <IconGripVertical
                              size={16}
                              style={{ cursor: "grab" }}
                            />
                            <Badge size="sm" variant="light">
                              {field.config?.type}
                            </Badge>
                            <Text size="sm" fw={500}>
                              {field.name}
                            </Text>
                          </Group>
                          <Group gap="xs">
                            <Tooltip label="Move Up">
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                disabled={index === 0}
                                onClick={() =>
                                  handleMoveUp(field.id, field.order ?? 0)
                                }
                              >
                                ↑
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Move Down">
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                disabled={
                                  index === formWithFields.fields.length - 1
                                }
                                onClick={() =>
                                  handleMoveDown(field.id, field.order ?? 0)
                                }
                              >
                                ↓
                              </ActionIcon>
                            </Tooltip>
                            <ActionIcon
                              size="sm"
                              variant="subtle"
                              color="red"
                              onClick={() => handleRemoveField(field.id)}
                            >
                              <IconTrash size={16} />
                            </ActionIcon>
                          </Group>
                        </Group>

                        <Divider />

                        <FieldPreview config={field.config!} />
                      </Stack>
                    </Card>
                  ))}
              </Stack>
            ) : (
              <Card withBorder p="xl">
                <Stack align="center" gap="md">
                  <Text size="lg" c="dimmed">
                    No fields added yet
                  </Text>
                  <Text size="sm" c="dimmed" ta="center">
                    Add fields from the right panel to start building your form
                  </Text>
                </Stack>
              </Card>
            )}
          </Paper>
        </Grid.Col>

        {/* Right Side - Available Fields */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper shadow="sm" p="md" withBorder style={{ position: "sticky", top: 20 }}>
            <Title order={3} mb="md">
              Available Fields
            </Title>
            <Text size="sm" c="dimmed" mb="md">
              Click to add a field to your form
            </Text>

            <ScrollArea h={600}>
              <Stack gap="sm">
                {fieldsNotInForm.length > 0 ? (
                  fieldsNotInForm.map((field) => (
                    <Card
                      key={field.id}
                      withBorder
                      p="sm"
                      style={{ cursor: "pointer" }}
                      onClick={() => handleAddField(field.id)}
                    >
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <Text size="sm" fw={500}>
                            {field.name}
                          </Text>
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="blue"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAddField(field.id);
                            }}
                          >
                            <IconPlus size={14} />
                          </ActionIcon>
                        </Group>
                        <Badge size="xs" variant="light">
                          {field.config?.type}
                        </Badge>
                        <Text size="xs" c="dimmed" lineClamp={2}>
                          {field.config?.label}
                        </Text>
                        {field.description && (
                          <Text size="xs" c="dimmed" lineClamp={1}>
                            {field.description}
                          </Text>
                        )}
                      </Stack>
                    </Card>
                  ))
                ) : (
                  <Text size="sm" c="dimmed" ta="center" py="xl">
                    All fields have been added.
                    <br />
                    <Button
                      component={Link}
                      href="/admin/forms/fields"
                      variant="subtle"
                      size="xs"
                      mt="sm"
                    >
                      Create new fields
                    </Button>
                  </Text>
                )}
              </Stack>
            </ScrollArea>
          </Paper>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}


"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Container,
  Title,
  Text,
  Paper,
  Stack,
  TextInput,
  Textarea,
  NumberInput,
  Checkbox,
  Select,
  Radio,
  MultiSelect,
  Slider,
  Button,
  Group,
  Loader,
  Center,
  Alert,
  Badge,
} from "@mantine/core";
import { DateInput } from "@mantine/dates";
import { IconAlertCircle } from "@tabler/icons-react";
import { api } from "~/trpc/react";
import type { FieldConfigType } from "~/server/db/schema";

interface FormFieldProps {
  field: {
    id: string;
    name: string;
    description: string | null;
    config: FieldConfigType | null;
    order: number | null;
  };
  value: any;
  onChange: (value: any) => void;
}

function FormField({ field, value, onChange }: FormFieldProps) {
  const config = field.config;

  if (!config) {
    return null;
  }

  switch (config.type) {
    case "text":
      return (
        <TextInput
          label={config.label}
          description={config.help}
          placeholder={config.placeholder}
          required={config.required}
          value={value || ""}
          onChange={(e) => onChange(e.currentTarget.value)}
        />
      );

    case "textarea":
      return (
        <Textarea
          label={config.label}
          description={config.help}
          placeholder={config.placeholder}
          required={config.required}
          rows={config.rows || 4}
          value={value || ""}
          onChange={(e) => onChange(e.currentTarget.value)}
        />
      );

    case "number":
      return (
        <NumberInput
          label={config.label}
          description={config.help}
          required={config.required}
          min={config.minValue}
          max={config.maxValue}
          value={value ?? config.defaultValue ?? null}
          onChange={onChange}
        />
      );

    case "date":
      return (
        <DateInput
          label={config.label}
          description={config.help}
          required={config.required}
          value={value ? new Date(value) : null}
          onChange={(date) => {
            if (date && typeof date === 'object' && 'toISOString' in date) {
              onChange((date as Date).toISOString());
            } else {
              onChange(null);
            }
          }}
        />
      );

    case "boolean":
      return (
        <Checkbox
          label={config.label}
          description={config.help}
          checked={value ?? config.defaultValue ?? false}
          onChange={(e) => onChange(e.currentTarget.checked)}
        />
      );

    case "select":
      return (
        <Select
          label={config.label}
          description={config.help}
          required={config.required}
          data={config.options}
          value={value || config.defaultValue || null}
          onChange={onChange}
        />
      );

    case "radio":
      return (
        <Radio.Group
          label={config.label}
          description={config.help}
          required={config.required}
          value={value || config.defaultValue || null}
          onChange={onChange}
        >
          <Stack mt="xs" gap="xs">
            {config.options.map((option) => (
              <Radio key={option} value={option} label={option} />
            ))}
          </Stack>
        </Radio.Group>
      );

    case "multiselect":
      return (
        <MultiSelect
          label={config.label}
          description={config.help}
          required={config.required}
          data={config.options}
          value={value || []}
          onChange={onChange}
          maxValues={config.maxSelections}
        />
      );

    case "slider":
      return (
        <div>
          <Text size="sm" fw={500} mb="xs">
            {config.label}
          </Text>
          {config.help && (
            <Text size="xs" c="dimmed" mb="xs">
              {config.help}
            </Text>
          )}
          <Slider
            value={value ?? config.defaultValue ?? config.options[0] ?? 0}
            onChange={onChange}
            min={Math.min(...config.options)}
            max={Math.max(...config.options)}
            marks={config.options.map((val) => ({ value: val, label: val.toString() }))}
          />
        </div>
      );

    case "discrete_range":
      return (
        <Radio.Group
          label={config.label}
          description={config.help}
          required={config.required}
          value={value?.toString() || null}
          onChange={(val) => onChange(val ? parseInt(val) : null)}
        >
          <Group mt="xs">
            {config.options.map((option) => (
              <Radio
                key={option.value}
                value={option.value.toString()}
                label={option.label}
              />
            ))}
          </Group>
        </Radio.Group>
      );

    default:
      return null;
  }
}

export default function FormPage({ params }: { params: Promise<{ form_id: string }> }) {
  const router = useRouter();
  const unwrappedParams = React.use(params);
  const formId = unwrappedParams.form_id;

  const [formData, setFormData] = useState<Record<string, any>>({});

  const { data: form, isLoading, error } = api.forms.getWithFields.useQuery({ id: formId });
  const { data: submission } = api.forms.getUserSubmission.useQuery({ formId });

  const submitMutation = api.forms.submitForm.useMutation({
    onSuccess: () => {
      alert("Formulář byl úspěšně odeslán!");
      router.push("/dashboard");
    },
    onError: (error) => {
      alert(`Chyba při odesílání formuláře: ${error.message}`);
    },
  });

  const saveDraftMutation = api.forms.saveDraft.useMutation({
    onSuccess: () => {
      alert("Koncept byl úspěšně uložen!");
    },
    onError: (error) => {
      alert(`Chyba při ukládání konceptu: ${error.message}`);
    },
  });

  // Load existing submission data
  React.useEffect(() => {
    if (submission?.submission?.data) {
      setFormData(submission.submission.data);
    }
  }, [submission]);

  const handleFieldChange = (fieldId: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [fieldId]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitMutation.mutate({ formId, data: formData });
  };

  const handleSaveDraft = () => {
    saveDraftMutation.mutate({ formId, data: formData });
  };

  const isSubmitted = submission?.userForm?.submission_status === "submitted";

  if (isLoading) {
    return (
      <Container size="md" py="xl">
        <Center h={400}>
          <Stack align="center" gap="md">
            <Loader size="lg" />
            <Text c="dimmed">Načítání formuláře...</Text>
          </Stack>
        </Center>
      </Container>
    );
  }

  if (error || !form) {
    return (
      <Container size="md" py="xl">
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="Chyba"
          color="red"
          variant="filled"
        >
          {error?.message || "Formulář nebyl nalezen"}
        </Alert>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Paper shadow="sm" p="xl" radius="md" withBorder>
        <Stack gap="lg">
          <div>
            <Group justify="space-between" align="flex-start">
              <div>
                <Title order={2} mb="xs">
                  {form.label}
                </Title>
                {form.description && (
                  <Text c="dimmed" size="sm">
                    {form.description}
                  </Text>
                )}
              </div>
              {isSubmitted && (
                <Badge color="green" size="lg" variant="filled">
                  Odesláno
                </Badge>
              )}
              {submission?.userForm?.submission_status === "draft" && (
                <Badge color="yellow" size="lg" variant="filled">
                  Koncept
                </Badge>
              )}
            </Group>
          </div>

          {isSubmitted && (
            <Alert color="green" variant="light">
              Tento formulář byl již odeslán. Můžete si níže prohlédnout své odpovědi, ale nemůžete je změnit.
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack gap="md">
              {form.fields && form.fields.length > 0 ? (
                form.fields.map((field) => (
                  <div key={field.id} style={{ pointerEvents: isSubmitted ? 'none' : 'auto', opacity: isSubmitted ? 0.7 : 1 }}>
                    <FormField
                      field={field}
                      value={formData[field.id]}
                      onChange={(value) => handleFieldChange(field.id, value)}
                    />
                  </div>
                ))
              ) : (
                <Alert color="blue" variant="light">
                  Tento formulář zatím nemá žádná pole.
                </Alert>
              )}

              {!isSubmitted && (
                <Group justify="space-between" mt="xl">
                  <Button variant="subtle" onClick={() => router.back()}>
                    Zrušit
                  </Button>
                  <Group>
                    <Button 
                      variant="light" 
                      onClick={handleSaveDraft}
                      disabled={form.fields?.length === 0}
                      loading={saveDraftMutation.isPending}
                    >
                      Uložit koncept
                    </Button>
                    <Button 
                      type="submit" 
                      disabled={form.fields?.length === 0}
                      loading={submitMutation.isPending}
                    >
                      Odeslat formulář
                    </Button>
                  </Group>
                </Group>
              )}

              {isSubmitted && (
                <Group justify="flex-end" mt="xl">
                  <Button variant="subtle" onClick={() => router.back()}>
                    Zpět na přehled
                  </Button>
                </Group>
              )}
            </Stack>
          </form>
        </Stack>
      </Paper>
    </Container>
  );
}
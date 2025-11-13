"use client";

import {
  TextInput,
  Textarea,
  NumberInput,
  Checkbox,
  Select,
  Radio,
  Group,
  Stack,
  Text,
  MultiSelect,
  Slider,
} from "@mantine/core";
import type { FieldConfigType } from "~/server/db/schema";

interface FieldPreviewProps {
  config: FieldConfigType;
}

export function FieldPreview({ config }: FieldPreviewProps) {
  const { label, required, help } = config;

  switch (config.type) {
    case "text":
      return (
        <TextInput
          label={label}
          placeholder={config.placeholder}
          description={help}
          required={required}
          disabled
        />
      );

    case "textarea":
      return (
        <Textarea
          label={label}
          placeholder={config.placeholder}
          description={help}
          required={required}
          rows={config.rows || 3}
          disabled
        />
      );

    case "date":
      return (
        <TextInput
          type="date"
          label={label}
          description={help}
          required={required}
          defaultValue={config.defaultValue}
          disabled
        />
      );

    case "number":
      return (
        <NumberInput
          label={label}
          description={help}
          required={required}
          min={config.minValue}
          max={config.maxValue}
          defaultValue={config.defaultValue}
          disabled
        />
      );

    case "boolean":
      return (
        <Checkbox
          label={label}
          description={help}
          defaultChecked={config.defaultValue}
          disabled
        />
      );

    case "select":
      return (
        <Select
          label={label}
          description={help}
          required={required}
          data={config.options}
          defaultValue={config.defaultValue}
          placeholder="Select an option"
          disabled
        />
      );

    case "radio":
      return (
        <Radio.Group
          label={label}
          description={help}
          required={required}
          defaultValue={config.defaultValue}
        >
          <Stack gap="xs" mt="xs">
            {config.options.map((option, idx) => (
              <Radio
                key={idx}
                value={option}
                label={option}
                disabled
              />
            ))}
          </Stack>
        </Radio.Group>
      );

    case "multiselect":
      return (
        <MultiSelect
          label={label}
          description={help}
          required={required}
          data={config.options}
          placeholder="Select options"
          maxValues={config.maxSelections}
          disabled
        />
      );

    case "slider":
      return (
        <Stack gap="xs">
          <div>
            <Text size="sm" fw={500}>
              {label}
              {required && <span style={{ color: "red" }}> *</span>}
            </Text>
            {help && (
              <Text size="xs" c="dimmed">
                {help}
              </Text>
            )}
          </div>
          <Slider
            defaultValue={config.defaultValue || config.options[0]}
            min={Math.min(...config.options)}
            max={Math.max(...config.options)}
            marks={config.options.map((val) => ({ value: val, label: val.toString() }))}
            step={null}
            disabled
          />
        </Stack>
      );

    case "discrete_range":
      return (
        <Stack gap="xs">
          <div>
            <Text size="sm" fw={500}>
              {label}
              {required && <span style={{ color: "red" }}> *</span>}
            </Text>
            {help && (
              <Text size="xs" c="dimmed">
                {help}
              </Text>
            )}
          </div>
          <Group gap="xs" wrap="wrap">
            {config.options.map((option, idx) => (
              <div
                key={idx}
                style={{
                  padding: "8px 16px",
                  border: "1px solid var(--mantine-color-gray-4)",
                  borderRadius: "4px",
                  cursor: "not-allowed",
                  opacity: 0.6,
                }}
              >
                <Text size="sm">{option.label}</Text>
              </div>
            ))}
          </Group>
        </Stack>
      );

    default:
      return (
        <Text size="sm" c="dimmed">
          Unknown field type: {(config as any).type}
        </Text>
      );
  }
}


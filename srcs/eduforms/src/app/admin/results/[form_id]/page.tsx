"use client";

import React from "react";
import { api } from "~/trpc/react";
import {
  Table,
  Button,
  Title,
  Text,
  Stack,
  Group,
  Paper,
  Loader,
  Center,
  Badge,
  ScrollArea,
} from "@mantine/core";
import {
  IconFileTypeCsv,
  IconFileTypeXls,
  IconDatabase,
  IconJson,
  IconArrowLeft,
} from "@tabler/icons-react";
import { useRouter, useParams } from "next/navigation";
import type { FieldConfigType } from "~/server/db/schema";

function formatFieldValue(value: any, fieldConfig?: FieldConfigType | null): string {
  if (value === null || value === undefined) return "—";
  
  if (typeof value === "boolean") return value ? "Ano" : "Ne";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  
  return String(value);
}

export default function SingleFormResultPage() {
  const router = useRouter();
  const params = useParams();
  const formId = params.form_id as string;

  const { data, isLoading, error } = api.forms.getFormSubmissions.useQuery({
    formId,
  });

  if (isLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    );
  }

  if (error) {
    return (
      <Center h={400}>
        <Stack align="center">
          <Text c="red">Chyba při načítání výsledků formuláře</Text>
          <Text size="sm" c="dimmed">{error.message}</Text>
        </Stack>
      </Center>
    );
  }

  if (!data) {
    return (
      <Center h={400}>
        <Text c="dimmed">Formulář nenalezen</Text>
      </Center>
    );
  }

  const { form, fields, submissions } = data;

  const handleExportMockup = (format: string) => {
    alert(`Export do ${format} - Funkce brzy dostupná!`);
  };

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-start">
        <Stack gap="xs">
          <Group>
            <Button
              variant="subtle"
              leftSection={<IconArrowLeft size={16} />}
              onClick={() => router.push("/admin/results")}
              size="sm"
            >
              Zpět na formuláře
            </Button>
          </Group>
          <Title order={2}>{form.label}</Title>
          {form.description && (
            <Text c="dimmed" size="sm">
              {form.description}
            </Text>
          )}
          <Badge color="blue" variant="light">
            {submissions.length} {submissions.length === 1 ? "odpověď" : submissions.length < 5 ? "odpovědi" : "odpovědí"}
          </Badge>
        </Stack>

        <Paper p="md" withBorder>
          <Stack gap="sm">
            <Text size="sm" fw={500}>
              Exportovat data
            </Text>
            <Group gap="xs">
              <Button
                size="xs"
                variant="light"
                leftSection={<IconFileTypeCsv size={16} />}
                onClick={() => handleExportMockup("CSV")}
              >
                CSV
              </Button>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconFileTypeXls size={16} />}
                onClick={() => handleExportMockup("Excel")}
              >
                Excel
              </Button>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconJson size={16} />}
                onClick={() => handleExportMockup("JSON")}
              >
                JSON
              </Button>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconDatabase size={16} />}
                onClick={() => handleExportMockup("SQLite")}
              >
                SQLite
              </Button>
            </Group>
          </Stack>
        </Paper>
      </Group>

      {submissions.length === 0 ? (
        <Paper shadow="sm" p="xl" withBorder>
          <Center>
            <Text c="dimmed">Zatím žádné odpovědi</Text>
          </Center>
        </Paper>
      ) : (
        <Paper shadow="sm" withBorder>
          <ScrollArea>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Uživatel</Table.Th>
                  <Table.Th>Email</Table.Th>
                  <Table.Th>Odesláno</Table.Th>
                  {fields.map((field) => (
                    <Table.Th key={field.id}>
                      {field.config?.label || field.name}
                    </Table.Th>
                  ))}
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {submissions.map((submission) => (
                  <Table.Tr key={submission.id}>
                    <Table.Td>
                      <Text size="sm" fw={500}>
                        {submission.user.name}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {submission.user.email}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {new Date(submission.createdAt).toLocaleString('cs-CZ')}
                      </Text>
                    </Table.Td>
                    {fields.map((field) => (
                      <Table.Td key={field.id}>
                        <Text size="sm">
                          {formatFieldValue(
                            submission.data?.[field.id],
                            field.config
                          )}
                        </Text>
                      </Table.Td>
                    ))}
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Paper>
      )}
    </Stack>
  );
}
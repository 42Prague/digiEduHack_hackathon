"use client";

import React from "react";
import { api } from "~/trpc/react";
import {
  Table,
  Badge,
  Button,
  Title,
  Text,
  Stack,
  Paper,
  Loader,
  Center,
} from "@mantine/core";
import { IconEye } from "@tabler/icons-react";
import { useRouter } from "next/navigation";

export default function FormListResults() {
  const router = useRouter();
  const { data: forms, isLoading } = api.forms.listFormsWithSubmissionCounts.useQuery();

  if (isLoading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    );
  }

  return (
    <Stack gap="lg">
      <div>
        <Title order={2}>Výsledky formulářů</Title>
        <Text c="dimmed" size="sm">
          Prohlížejte a stahujte data ze všech formulářů
        </Text>
      </div>

      <Paper shadow="sm" p="md" withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Název formuláře</Table.Th>
              <Table.Th>Popis</Table.Th>
              <Table.Th>Odpovědi</Table.Th>
              <Table.Th>Vytvořeno</Table.Th>
              <Table.Th>Akce</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {forms && forms.length > 0 ? (
              forms.map((form) => (
                <Table.Tr key={form.id}>
                  <Table.Td>
                    <Text fw={500}>{form.label}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" lineClamp={1}>
                      {form.description || "Bez popisu"}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge
                      color={form.submissionCount > 0 ? "blue" : "gray"}
                      variant="light"
                    >
                      {form.submissionCount} {form.submissionCount === 1 ? "odpověď" : form.submissionCount < 5 ? "odpovědi" : "odpovědí"}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {new Date(form.createdAt).toLocaleDateString('cs-CZ')}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Button
                      size="xs"
                      variant="light"
                      leftSection={<IconEye size={16} />}
                      onClick={() => router.push(`/admin/results/${form.id}`)}
                      disabled={form.submissionCount === 0}
                    >
                      Zobrazit výsledky
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))
            ) : (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Center py="xl">
                    <Text c="dimmed">Žádné formuláře</Text>
                  </Center>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  );
}
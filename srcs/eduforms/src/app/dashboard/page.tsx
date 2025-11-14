"use client";

import { Container, Title, Text, Card, Group, Stack, Badge, Button } from "@mantine/core";
import { api } from "~/trpc/react";
import Link from "next/link";

export default function UserDashboard() {
  const { data: forms, isLoading } = api.forms.listWithStatus.useQuery();

  if (isLoading) {
    return (
      <Container size="lg" py="xl">
        <Text>Loading forms...</Text>
      </Container>
    );
  }

  const getStatusBadge = (status: string | null) => {
    if (status === "submitted") {
      return <Badge color="green" variant="filled">Submitted</Badge>;
    }
    if (status === "draft") {
      return <Badge color="yellow" variant="light">Draft</Badge>;
    }
    return <Badge color="blue" variant="light">Not Started</Badge>;
  };

  const getButtonText = (status: string | null) => {
    if (status === "submitted") {
      return "View Submission";
    }
    if (status === "draft") {
      return "Continue Draft";
    }
    return "Start Form";
  };

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <div>
          <Title order={1} mb="xs">Available Forms</Title>
          <Text c="dimmed">Complete the forms below</Text>
        </div>

        {forms && forms.length > 0 ? (
          <Stack gap="md">
            {forms.map((form) => (
              <Card key={form.id} shadow="sm" padding="lg" radius="md" withBorder>
                <Stack gap="sm">
                  <Group justify="space-between" align="flex-start">
                    <div style={{ flex: 1 }}>
                      <Title order={3} mb="xs">{form.label}</Title>
                      {form.description && (
                        <Text size="sm" c="dimmed">{form.description}</Text>
                      )}
                    </div>
                    {getStatusBadge(form.submissionStatus)}
                  </Group>
                  
                  <Group justify="flex-end">
                    <Button
                      component={Link}
                      href={`/dashboard/forms/${form.id}`}
                      variant={form.submissionStatus === "submitted" ? "light" : "filled"}
                    >
                      {getButtonText(form.submissionStatus)}
                    </Button>
                  </Group>
                </Stack>
              </Card>
            ))}
          </Stack>
        ) : (
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text c="dimmed" ta="center">No forms available at the moment</Text>
          </Card>
        )}
      </Stack>
    </Container>
  );
}
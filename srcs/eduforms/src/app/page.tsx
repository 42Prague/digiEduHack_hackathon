"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Anchor,
  Badge,
  Button,
  Divider,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
  Alert,
  Group,
} from '@mantine/core';
import { IconAlertCircle, IconShield } from '@tabler/icons-react';
import classes from './AuthenticationImage.module.css';
import { authClient } from '~/server/better-auth/client';

export default function Home() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const router = useRouter();

  const handleLogin = async () => {
    // Reset error state
    setError(null);
    
    // Validation
    if (!email || !password) {
      setError(isAdminMode ? 'Please enter email and password.' : 'Prosím vyplňte e-mail a heslo.');
      return;
    }

    setIsLoading(true);

    try {
      const { data, error } = await authClient.signIn.email({
        email,
        password,
        callbackURL: isAdminMode ? "/admin" : "/dashboard",
        rememberMe: false
      });

      if (error) {
        setError(isAdminMode 
          ? 'Invalid credentials or insufficient permissions.' 
          : 'Neplatný e-mail nebo heslo. Zkontrolujte své přihlašovací údaje.'
        );
        setIsLoading(false);
        return;
      }

      // Successfully logged in
      if (data) {
        router.push(isAdminMode ? '/admin' : '/dashboard');
      }
    } catch (err) {
      setError(isAdminMode 
        ? 'An error occurred during login. Please try again.' 
        : 'Došlo k chybě při přihlašování. Zkuste to prosím znovu.'
      );
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsAdminMode(!isAdminMode);
    setEmail('');
    setPassword('');
    setError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleLogin();
    }
  }; 

  return (
    <div className={classes.wrapper}>
      <Paper className={classes.form} radius="lg">
        <Stack gap="md">
          {isAdminMode ? (
            // Admin Login Form
            <>
              <Stack gap="xs" align="center">
                <Badge size="md" radius="sm" variant="light" color="red">
                  <Group gap={4}>
                    <IconShield size={14} />
                    Admin Access
                  </Group>
                </Badge>
                <Title order={3} className={classes.title}>
                  Admin Login
                </Title>
              </Stack>

              {error && (
                <Alert 
                  icon={<IconAlertCircle size={16} />} 
                  color="red"
                  radius="md"
                >
                  {error}
                </Alert>
              )}

              <Stack gap="sm">
                <TextInput
                  label="Email"
                  placeholder="admin@eduforms.org"
                  size="sm"
                  radius="md"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.currentTarget.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
                <PasswordInput
                  label="Password"
                  placeholder="Enter password"
                  size="sm"
                  radius="md"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.currentTarget.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
              </Stack>

              <Button
                fullWidth
                size="sm"
                radius="md"
                variant="filled"
                color="red"
                onClick={handleLogin}
                loading={isLoading}
              >
                Login
              </Button>
            </>
          ) : (
            // Teacher Login Form
            <>
              <Stack gap="xs" align="center">
                <Badge size="md" radius="sm" variant="light" color="blue">
                  EduForms
                </Badge>
                <Title order={3} className={classes.title}>
                  Vítejte zpět
                </Title>
              </Stack>

              {error && (
                <Alert 
                  icon={<IconAlertCircle size={16} />} 
                  color="red"
                  radius="md"
                >
                  {error}
                </Alert>
              )}

              <Stack gap="sm">
                <TextInput
                  label="E-mail"
                  placeholder="jmeno.prijmeni@skola.cz"
                  size="sm"
                  radius="md"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.currentTarget.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
                <PasswordInput
                  label="Heslo"
                  placeholder="Zadejte heslo"
                  size="sm"
                  radius="md"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.currentTarget.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
              </Stack>

              <Button
                fullWidth
                size="sm"
                radius="md"
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan' }}
                onClick={handleLogin}
                loading={isLoading}
              >
                Přihlásit
              </Button>
            </>
          )}

          {/* Toggle button at the bottom */}
          <Divider />
          <Group justify="center">
            <Button
              variant="subtle"
              size="xs"
              color="gray"
              leftSection={<IconShield size={14} />}
              onClick={toggleMode}
              disabled={isLoading}
            >
              {isAdminMode ? 'Teacher Login' : 'Admin'}
            </Button>
          </Group>
        </Stack>
      </Paper>
    </div>
  );
}

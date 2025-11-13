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
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import classes from './AuthenticationImage.module.css';
import { authClient } from '~/server/better-auth/client';

export default function Home() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleLogin = async () => {
    // Reset error state
    setError(null);
    
    // Validation
    if (!email || !password) {
      setError('Prosím vyplňte e-mail a heslo.');
      return;
    }

    setIsLoading(true);

    try {
      const { data, error } = await authClient.signIn.email({
        email,
        password,
        callbackURL: "/dashboard",
        rememberMe: false
      });

      if (error) {
        setError('Neplatný e-mail nebo heslo. Zkontrolujte své přihlašovací údaje.');
        setIsLoading(false);
        return;
      }

      // Successfully logged in
      if (data) {
        router.push('/dashboard');
      }
    } catch (err) {
      setError('Došlo k chybě při přihlašování. Zkuste to prosím znovu.');
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleLogin();
    }
  }; 

  return (
    <div className={classes.wrapper}>
      <Paper className={classes.form} radius="lg">
        <Stack gap="lg">
          <Stack gap="xs" align="center">
            <Badge size="lg" radius="sm" variant="light" color="blue">
              Přístup pro pedagogy EduForms
            </Badge>
            <Title order={2} className={classes.title}>
              Vítejte zpět, učitelé
            </Title>
            <Text ta="center" c="dimmed">
              Přihlaste se pomocí institucionální e-mailové adresy a hesla, které jste obdrželi v
              uvítacím e-mailu. Po přihlášení si je můžete upravit přímo v portálu.
            </Text>
          </Stack>

          {error && (
            <Alert 
              icon={<IconAlertCircle size={16} />} 
              title="Chyba přihlášení" 
              color="red"
              radius="md"
            >
              {error}
            </Alert>
          )}

          <Stack gap="sm">
            <TextInput
              label="Institucionální e-mail"
              placeholder="jmeno.prijmeni@skola.cz"
              size="md"
              radius="md"
              required
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              description="Použijte školní e-mail, který vám sdělil váš koordinátor."
            />
            <PasswordInput
              label="Přidělené heslo"
              placeholder="Zadejte dočasné heslo"
              size="md"
              radius="md"
              required
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              description="Opíšete přístupový kód z uvítacího e-mailu přesně tak, jak vám přišel."
            />
          </Stack>

          <Text size="sm" c="dimmed">
            Tip: Pokud nemůžete své přihlašovací údaje najít, vyhledejte e-mail s předmětem
            &quot;EDUZměna Přístupové údaje&quot; nebo požádejte koordinátora o nové zaslání.
          </Text>

          <Button
            fullWidth
            size="md"
            radius="md"
            variant="gradient"
            gradient={{ from: 'blue', to: 'cyan' }}
            onClick={handleLogin}
            loading={isLoading}
          >
            Bezpečně přihlásit
          </Button>

          <Divider label="Potřebujete pomoc?" labelPosition="center" />

          <Text size="sm" c="dimmed" ta="center">
            Stále vám chybí e-mail nebo heslo? Obraťte se na svého koordinátora nebo napište na{' '}
            <Anchor href="mailto:help@eduforms.org">help@eduforms.org</Anchor> a my vás připojíme.
          </Text>
        </Stack>
      </Paper>
    </div>
  );
}

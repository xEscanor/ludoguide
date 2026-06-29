// LudoRef — Supabase client partagé
// Chargé sur toutes les pages qui nécessitent l'auth

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const SUPABASE_URL = 'https://nkjgsmbrjwlxijjljzne.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ramdzbWJyandseGlqamxqem5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI3NDY3MTksImV4cCI6MjA5ODMyMjcxOX0.UhQda66OgCosrZs_UmcfLQO8E3loamGeBhXAyf1VNok';

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Retourne l'utilisateur connecté ou null
export async function getUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

// Connexion Google
export async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: 'https://ludoref.fr/mon-compte.html' }
  });
  if (error) console.error('Google auth error:', error);
}

// Connexion email/password
export async function signInWithEmail(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  return { data, error };
}

// Inscription email/password
export async function signUpWithEmail(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email, password,
    options: { emailRedirectTo: 'https://ludoref.fr/mon-compte.html' }
  });
  return { data, error };
}

// Déconnexion
export async function signOut() {
  await supabase.auth.signOut();
  window.location.href = '/';
}

// Ludothèque — ajouter/modifier un jeu
export async function upsertGame(slug, status, rating = null) {
  const user = await getUser();
  if (!user) return { error: 'Non connecté' };
  const { data, error } = await supabase
    .from('user_games')
    .upsert({ user_id: user.id, game_slug: slug, status, rating },
            { onConflict: 'user_id,game_slug' });
  return { data, error };
}

// Ludothèque — supprimer un jeu
export async function removeGame(slug) {
  const user = await getUser();
  if (!user) return { error: 'Non connecté' };
  const { error } = await supabase
    .from('user_games')
    .delete()
    .eq('user_id', user.id)
    .eq('game_slug', slug);
  return { error };
}

// Ludothèque — récupérer tous les jeux de l'utilisateur
export async function getUserGames() {
  const user = await getUser();
  if (!user) return [];
  const { data, error } = await supabase
    .from('user_games')
    .select('*')
    .eq('user_id', user.id);
  return error ? [] : data;
}

// Ludothèque — statut d'un jeu précis
export async function getGameStatus(slug) {
  const user = await getUser();
  if (!user) return null;
  const { data } = await supabase
    .from('user_games')
    .select('*')
    .eq('user_id', user.id)
    .eq('game_slug', slug)
    .single();
  return data;
}

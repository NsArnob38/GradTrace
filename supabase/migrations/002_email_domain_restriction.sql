-- GradeTrace — Restrict auth to @northsouth.edu emails only
-- Run this in Supabase SQL Editor

-- This function runs BEFORE a new user is created.
-- It blocks any email that doesn't end with @northsouth.edu
CREATE OR REPLACE FUNCTION public.check_email_domain()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.email IS NOT NULL AND NEW.email NOT LIKE '%@northsouth.edu' THEN
    RAISE EXCEPTION 'Only @northsouth.edu email addresses are allowed to sign up.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if any
DROP TRIGGER IF EXISTS enforce_email_domain ON auth.users;

-- Create trigger that fires before insert
CREATE TRIGGER enforce_email_domain
  BEFORE INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.check_email_domain();

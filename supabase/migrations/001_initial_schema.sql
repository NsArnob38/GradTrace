-- GradeTrace — Initial Database Schema
-- Supabase Migration 001

-- ═══════════════════════════════════════════════════
-- TABLES
-- ═══════════════════════════════════════════════════

-- User profiles (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  student_id TEXT UNIQUE,
  email TEXT UNIQUE,
  role TEXT CHECK (role IN ('student', 'admin')) DEFAULT 'student',
  program TEXT CHECK (program IN ('CSE', 'BBA')),
  bba_concentration TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploaded transcripts
CREATE TABLE transcripts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  file_name TEXT,
  raw_data JSONB,
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cached audit results
CREATE TABLE audit_results (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  level_1 JSONB,
  level_2 JSONB,
  level_3 JSONB,
  roadmap JSONB,
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Curriculum definitions
CREATE TABLE programs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  program_code TEXT NOT NULL,
  course_code TEXT NOT NULL,
  course_name TEXT NOT NULL,
  credits INT NOT NULL,
  category TEXT NOT NULL
);

-- Scan/audit history
CREATE TABLE scan_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
  audit_result_id UUID REFERENCES audit_results(id) ON DELETE CASCADE,
  input_type TEXT CHECK (input_type IN ('csv', 'image', 'pdf', 'xlsx', 'txt')) DEFAULT 'csv',
  file_name TEXT,
  scanned_at TIMESTAMPTZ DEFAULT NOW(),
  summary JSONB
);

-- ═══════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;

-- Profiles: users see/edit own, admins see all
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Admins can view all profiles"
  ON profiles FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Transcripts: users see/create own, admins see all
CREATE POLICY "Users can view own transcripts"
  ON transcripts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own transcripts"
  ON transcripts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Admins can view all transcripts"
  ON transcripts FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Audit results: users can read own, never writable by client
CREATE POLICY "Users can view own audit results"
  ON audit_results FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Admins can view all audit results"
  ON audit_results FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Programs: everyone can read, admins can modify
CREATE POLICY "Anyone can read programs"
  ON programs FOR SELECT USING (true);
CREATE POLICY "Admins can manage programs"
  ON programs FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Scan history: users see own, admins see all
CREATE POLICY "Users can view own scan history"
  ON scan_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own scan history"
  ON scan_history FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Admins can view all scan history"
  ON scan_history FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- ═══════════════════════════════════════════════════
-- AUTO-CREATE PROFILE ON SIGNUP
-- ═══════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ═══════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════

CREATE INDEX idx_transcripts_user_id ON transcripts(user_id);
CREATE INDEX idx_audit_results_user_id ON audit_results(user_id);
CREATE INDEX idx_audit_results_transcript_id ON audit_results(transcript_id);
CREATE INDEX idx_scan_history_user_id ON scan_history(user_id);

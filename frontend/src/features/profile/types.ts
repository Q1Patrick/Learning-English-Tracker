export interface LearningProfile {
  displayName: string
  englishLevel: string
  dailyTargetMinutes: number
  learningGoal: string
  timezone: string
}

export interface CurrentUserProfile {
  email: string
  profile: LearningProfile | null
}

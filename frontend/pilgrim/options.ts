// Tap-first option sets — values mirror the dataset columns exactly so a tapped report
// maps straight onto Synthetic_Missing_Persons_2500.csv (gender, age_band, last_seen_location).
import type { OptStrings } from "./i18n";

export type GenderValue = "Male" | "Female" | "Unknown";

export const GENDERS: { value: GenderValue; icon: string; key: keyof Pick<OptStrings, "male" | "female" | "notSure"> }[] = [
  { value: "Male", icon: "👨", key: "male" },
  { value: "Female", icon: "👩", key: "female" },
  { value: "Unknown", icon: "❔", key: "notSure" },
];

// age_band values are numeric ranges → universal, no translation needed; icon conveys meaning.
export const AGE_BANDS: { value: string; icon: string }[] = [
  { value: "0-12", icon: "🧒" },
  { value: "13-17", icon: "🧑" },
  { value: "18-40", icon: "🧑" },
  { value: "41-60", icon: "🧔" },
  { value: "61-70", icon: "👴" },
  { value: "71-80", icon: "👵" },
  { value: "80+", icon: "👴" },
];

// The 20 real last_seen_location values present in the dataset (place names, kept as-is).
export const LOCATIONS: string[] = [
  "Adgaon Parking",
  "Bus Stand Nashik",
  "Dasak Ghat",
  "Dindori Road Crossing",
  "Gauri Patangan",
  "Kapila Sangam",
  "Kushavart Kund",
  "Laxmi Narayan Ghat",
  "Madsangvi Transit",
  "Main Police Chowki",
  "Nandur Ghat",
  "Nashik Road Station",
  "Panchavati Circle",
  "Rajur Bahula",
  "Ramkund Ghat",
  "Sadhugram Gate 1",
  "Sadhugram Gate 2",
  "Takli Sangam",
  "Trimbak Road",
  "Trimbakeshwar Approach",
];

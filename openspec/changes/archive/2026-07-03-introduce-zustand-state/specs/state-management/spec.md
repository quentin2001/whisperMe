# Zustand State Specs

## ADDED Requirements

### Requirement: Granular Subscriptions
React components MUST use selector functions when consuming state from Zustand to avoid unnecessary re-renders.

#### Scenario: Audio playback progress
- Given the audio player is playing and updating `currentTime`
- When `usePlayerStore((state) => state.currentTime)` changes
- Then only the player component should re-render, and the root `App` component MUST NOT re-render.

### Requirement: Store Segregation
State MUST be logically separated into domain-specific stores rather than a single monolithic store.
- Player states -> `playerStore`
- Configuration -> `configStore`
- Tasks & Data -> `taskStore`
- UI & Navigation -> `uiStore`

#### Scenario: Code modularity validation
- Given a developer wants to access the current configuration
- When they import a store hook
- Then they must import `useConfigStore` instead of a generic `useStore`.

Feature: <!-- feature name -->

  # Gate 1 BDD template

  # Each scenario must map to one or more EARS IDs and declare its acceptance type.
  # Acceptance types: automated, semi-automated, manual-only, not-scenario-suitable.
  @EARS-xxx @ACCEPTANCE-automated
  Scenario: <!-- BDD-SCENARIO-xxx: scenario title -->
    Given <!-- context -->
    When <!-- action -->
    Then <!-- expected result -->

  # Do not add behavior that is absent from PRD/EARS.
  # Every critical EARS requirement needs at least one scenario or an explicit exception reason.

from django.core.management.base import BaseCommand
from scraper.models import Workspace, Interaction


class Command(BaseCommand):
    help = 'Create a default example workspace with Alzheimer\'s disease interactions'

    def handle(self, *args, **options):
        # Check if default workspace already exists
        if Workspace.objects.filter(name="Example: Alzheimer's Disease Research").exists():
            self.stdout.write(self.style.WARNING('Default workspace already exists. Skipping.'))
            return

        self.stdout.write('Creating default Alzheimer\'s workspace...')

        # Create workspace
        workspace = Workspace.objects.create(
            name="Example: Alzheimer's Disease Research",
            initial_variable="Amyloid Beta Plaques"
        )

        # Alzheimer's interactions data
        interactions_data = [
            ("Amyloid Beta Plaques", "Synaptic Function", "-"),
            ("Amyloid Beta Plaques", "Neuroinflammation", "+"),
            ("Amyloid Beta Plaques", "Tau Protein Phosphorylation", "+"),
            ("Amyloid Beta Plaques", "BDNF Levels", "-"),
            ("Tau Protein Phosphorylation", "Neurofibrillary Tangles", "+"),
            ("Neurofibrillary Tangles", "Neuronal Death", "+"),
            ("Neuroinflammation", "Microglial Activation", "+"),
            ("Neuroinflammation", "Acetylcholine Levels", "-"),
            ("Microglial Activation", "Cytokine Release", "+"),
            ("Cytokine Release", "Blood-Brain Barrier Permeability", "+"),
            ("Cytokine Release", "Neuronal Death", "+"),
            ("Synaptic Function", "Memory Formation", "+"),
            ("Synaptic Function", "Cognitive Function", "+"),
            ("Neuronal Death", "Hippocampal Volume", "-"),
            ("Neuronal Death", "Cortical Thickness", "-"),
            ("Hippocampal Volume", "Memory Formation", "+"),
            ("Cortical Thickness", "Executive Function", "+"),
            ("Oxidative Stress", "Mitochondrial Dysfunction", "+"),
            ("Oxidative Stress", "DNA Damage", "+"),
            ("Mitochondrial Dysfunction", "ATP Production", "-"),
            ("ATP Production", "Synaptic Function", "+"),
            ("DNA Damage", "Neuronal Death", "+"),
            ("Acetylcholine Levels", "Memory Formation", "+"),
            ("Acetylcholine Levels", "Attention", "+"),
            ("BDNF Levels", "Neurogenesis", "+"),
            ("BDNF Levels", "Synaptic Plasticity", "+"),
            ("Neurogenesis", "Hippocampal Volume", "+"),
            ("Synaptic Plasticity", "Learning Ability", "+"),
            ("Insulin Resistance", "Glucose Metabolism", "-"),
            ("Glucose Metabolism", "ATP Production", "+"),
            ("Insulin Resistance", "Amyloid Beta Plaques", "+"),
            ("Blood-Brain Barrier Permeability", "Amyloid Beta Clearance", "-"),
            ("Amyloid Beta Clearance", "Amyloid Beta Plaques", "-"),
            ("Sleep Quality", "Amyloid Beta Clearance", "+"),
            ("Sleep Quality", "Memory Consolidation", "+"),
            ("Physical Exercise", "BDNF Levels", "+"),
            ("Physical Exercise", "Cerebral Blood Flow", "+"),
            ("Cerebral Blood Flow", "Oxygen Delivery", "+"),
            ("Oxygen Delivery", "ATP Production", "+"),
            ("Social Engagement", "Cognitive Reserve", "+"),
            ("Cognitive Reserve", "Cognitive Function", "+"),
        ]

        # Create interactions
        created_count = 0
        for iv, dv, effect in interactions_data:
            Interaction.objects.create(
                workspace=workspace,
                independent_variable=iv,
                dependent_variable=dv,
                effect=effect,
                reference="10.1038/example",
                date_published="2023"
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created default workspace with {created_count} interactions!'
            )
        )

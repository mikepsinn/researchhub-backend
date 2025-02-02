from rest_framework.test import APITestCase

from paper.exceptions import DuplicatePaperError
from paper.models import PaperSubmission
from paper.tasks import celery_create_paper, celery_crossref, celery_get_doi
from user.tests.helpers import create_random_default_user


class PaperSubmissionViewTests(APITestCase):
    def setUp(self):
        self.url = "https://spj.sciencemag.org/journals/plantphenomics/2020/8086309/"
        self.duplicate_url = "https://www.vitisgen2.org/research-in-plain-english/evaluating-and-mapping-grape-color-using-image-based-phenotyping/"
        self.true_doi = "10.34133/2020/8086309"
        self.submitter = create_random_default_user("submitter")
        self.client.force_authenticate(self.submitter)

        # Creating a submission
        self.paper_submission = PaperSubmission.objects.create(
            url=self.url,
            uploaded_by=self.submitter,
        )
        self.duplicate_paper_submission = PaperSubmission.objects.create(
            url=self.url,
            uploaded_by=self.submitter,
        )

    def test_full_flow(self):
        self.client.force_authenticate(self.submitter)
        self._paper_submission_flow()
        self._duplicate_doi_flow()

    def _paper_submission_flow(self):
        celery_data = (
            {"dois": [], "url": self.url, "uploaded_by_id": self.submitter.id},
            self.paper_submission.id,
        )

        celery_data_after_doi = celery_get_doi.apply((celery_data,)).result
        dois = celery_data_after_doi[0]["dois"]
        self.assertIn(self.true_doi, dois)

        celery_data_after_crossref = celery_crossref.apply((celery_data,)).result
        doi = celery_data_after_crossref[0]["doi"]
        self.assertEqual(self.true_doi, doi)

        paper_id = celery_create_paper.apply((celery_data,)).result
        self.assertEqual(isinstance(paper_id, int), True)

    def _duplicate_doi_flow(self):
        self.client.force_authenticate(self.submitter)
        celery_data = (
            {
                "dois": [],
                "url": self.duplicate_url,
                "uploaded_by_id": self.submitter.id,
            },
            self.duplicate_paper_submission.id,
        )

        celery_data_after_doi = celery_get_doi.apply((celery_data,)).result
        dois = celery_data_after_doi[0]["dois"]
        self.assertIn(self.true_doi, dois)

        celery_data_after_crossref = celery_crossref.apply((celery_data,)).result
        self.assertEqual(
            isinstance(celery_data_after_crossref, DuplicatePaperError), True
        )

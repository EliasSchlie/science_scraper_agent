import os
import re
import json
import urllib.request
import urllib.parse
from typing import Optional

try:
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False


class PDFFromDOI:
    def __init__(self, output_dir: str = None, brightdata_api_key: Optional[str] = None, unpaywall_email: str = "test@google.com") -> None:
        if output_dir is None and DJANGO_AVAILABLE:
            output_dir = os.path.join(settings.BASE_DIR, 'media', 'pdfs')
        elif output_dir is None:
            output_dir = "pdfs"
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.brightdata_api_key = brightdata_api_key or os.environ.get("BRIGHT_WEB_UNLOCKER_KEY")
        self.unpaywall_email = unpaywall_email

    def download(self, doi: str, filename: str = None, progress_callback=None) -> Optional[str]:
        def log(msg):
            if progress_callback:
                progress_callback(msg)
            print(msg)

        path = os.path.join(self.output_dir, f"{self._sanitize_filename(filename or doi)}.pdf")

        # Try arXiv direct download first if it's an arXiv DOI
        if self._is_arxiv_doi(doi):
            log("📋 Detected arXiv DOI, trying direct download...")
            pdf_url = self._get_arxiv_pdf_url(doi)
            if pdf_url and self._download_pdf_direct(pdf_url, path):
                self._validate_pdf(path)
                return path

        # Fallback to Unpaywall
        log("🔍 Querying Unpaywall API...")
        try:
            pdf_url = self._get_pdf_url_from_unpaywall(doi)
            log(f"✓ Found PDF URL: {pdf_url[:50]}...")
        except Exception as e:
            log(f"✗ Unpaywall failed: {str(e)}")
            raise

        if not pdf_url:
            raise FileNotFoundError(f"No open-access PDF found for DOI: {doi}")

        # Try Bright Data first, fallback to direct download
        if self.brightdata_api_key:
            log("📥 Attempting download via Bright Data...")
            if self._download_pdf_via_brightdata(pdf_url, path):
                self._validate_pdf(path)
                return path
            log("✗ Bright Data failed, trying direct download...")

        log("📥 Attempting direct download...")
        if self._download_pdf_direct(pdf_url, path):
            self._validate_pdf(path)
            return path

        raise RuntimeError(f"Failed to download PDF from: {pdf_url}")

    def _get_pdf_url_from_unpaywall(self, doi: str) -> str:
        base = "https://api.unpaywall.org/v2/"
        url = f"{base}{urllib.parse.quote(doi)}?{urllib.parse.urlencode({'email': self.unpaywall_email})}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        try:
            # Reduced timeout to 5 seconds - Unpaywall should be fast
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                raise RuntimeError(f"Unpaywall connection failed: {e.reason}") from e
            elif hasattr(e, 'code'):
                raise RuntimeError(f"Unpaywall returned error {e.code}") from e
            raise RuntimeError(f"Unpaywall lookup failed for DOI: {doi}") from e
        except Exception as e:
            raise RuntimeError(f"Unpaywall lookup failed for DOI: {doi} - {type(e).__name__}: {str(e)}") from e
        best = data.get("best_oa_location") or {}
        pdf_url = best.get("url_for_pdf")
        if not pdf_url:
            raise FileNotFoundError(f"No open-access PDF URL in Unpaywall response for DOI: {doi}")
        print(pdf_url)
        return pdf_url

    def _download_pdf_via_brightdata(self, pdf_url: str, out_path: str) -> bool:
        if not self.brightdata_api_key:
            return False
        body = json.dumps({"zone": "web_unlocker1", "url": pdf_url, "format": "raw"}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.brightdata.com/request",
            data=body,
            headers={"Authorization": f"Bearer {self.brightdata_api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            # Bright Data can be slow for complex pages - give it more time
            with urllib.request.urlopen(req, timeout=45) as resp, open(out_path, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as e:
            print(f"Bright Data download failed: {e}")
            return False

    def _download_pdf_direct(self, pdf_url: str, out_path: str) -> bool:
        """Direct download fallback for open-access PDFs"""
        try:
            req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            # Reduced timeout to 10 seconds
            with urllib.request.urlopen(req, timeout=10) as resp, open(out_path, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as e:
            print(f"Direct download failed: {e}")
            return False

    def _is_arxiv_doi(self, doi: str) -> bool:
        """Check if DOI is from arXiv (format: 10.48550/arXiv.XXXX)"""
        return doi.startswith("10.48550/arXiv.")
    
    def _get_arxiv_pdf_url(self, doi: str) -> str:
        """Extract arXiv ID from DOI and construct PDF URL"""
        if not self._is_arxiv_doi(doi):
            raise ValueError(f"Not an arXiv DOI: {doi}")
        arxiv_id = doi.split("arXiv.")[-1]
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    def _validate_pdf(self, path: str) -> None:
        """Check if file is actually a PDF, raise error if not"""
        with open(path, "rb") as f:
            if f.read(5) != b"%PDF-":
                os.remove(path)
                raise RuntimeError(f"Downloaded file is HTML, not PDF (likely paywalled)")
    
    def _sanitize_filename(self, filename: str) -> str:
        return re.sub(r"[\\/*?:\"<>|]", "_", filename)

if __name__ == "__main__":
    pdf_from_doi = PDFFromDOI()
    path = pdf_from_doi.download("10.1001/jamacardio.2016.2415")
    print(path)
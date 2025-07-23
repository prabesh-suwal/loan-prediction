import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.services.loan_service import LoanService
from app.core.models.schemas import LoanApplicationInput
from app.utils.exceptions import ValidationError

class TestLoanService:
    """Test cases for LoanService."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        return {
            'loan_repository': Mock(),
            'weight_repository': Mock(),
            'predictor': Mock(),
            'explainer': Mock()
        }
    
    @pytest.fixture
    def loan_service(self, mock_dependencies):
        """Create LoanService with mocked dependencies."""
        return LoanService(**mock_dependencies)
    
    @pytest.fixture
    def sample_application(self):
        """Sample loan application data."""
        return LoanApplicationInput(
            gender="Male",
            married="Yes",
            dependents=1,
            education="Graduate",
            self_employed="No",
            applicant_income=5849,
            coapplicant_income=0,
            loan_amount=128,
            loan_amount_term=360,
            credit_history=1,
            property_area="Urban"
        )
    
    @pytest.mark.asyncio
    async def test_process_loan_application_success(
        self, 
        loan_service, 
        sample_application, 
        mock_dependencies
    ):
        """Test successful loan application processing."""
        
        # Setup mocks
        mock_dependencies['weight_repository'].get_active_weights = AsyncMock(
            return_value={'credit_history': 2.5}
        )
        mock_dependencies['predictor'].predict.return_value = {
            'loan_decision': 'Yes',
            'risk_score': 22,
            'risk_category': 'Low',
            'recommendation': 'Approve',
            'confidence_score': 0.87
        }
        mock_dependencies['explainer'].generate_explanation.return_value = (
            "Approved due to good credit history and manageable EMI burden."
        )
        mock_dependencies['loan_repository'].create_application = AsyncMock(
            return_value=Mock()
        )
        
        # Execute
        result = await loan_service.process_loan_application(sample_application)
        
        # Verify
        assert result.loan_decision == "Yes"
        assert result.risk_score == 22
        assert result.risk_category == "Low"
        assert result.recommendation == "Approve"
        assert "good credit history" in result.justification
        
        # Verify mock calls
        mock_dependencies['predictor'].predict.assert_called_once()
        mock_dependencies['loan_repository'].create_application.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_loan_application_validation_error(
        self, 
        loan_service
    ):
        """Test loan application with validation error."""
        
        # Create invalid application (negative income)
        invalid_app = LoanApplicationInput(
            gender="Male",
            married="Yes", 
            dependents=1,
            education="Graduate",
            self_employed="No",
            applicant_income=-1000,  # Invalid
            coapplicant_income=0,
            loan_amount=128,
            loan_amount_term=360,
            credit_history=1,
            property_area="Urban"
        )
        
        # Should raise ValidationError
        with pytest.raises(ValidationError):
            await loan_service.process_loan_application(invalid_app)

if __name__ == "__main__":
    pytest.main([__file__])
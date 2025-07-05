#!/usr/bin/env python3
"""
Reppo Solver Node - Main orchestrator class
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Import components
from datasolver.datasolver import DataSolver
import ipfsUploader
import nftAuthorizer
import submitSolution
import rfdListener

logger = logging.getLogger('SolverNode')

class SolverNode:
    """Main solver node orchestrator"""
    
    def __init__(self, test_mode: bool = False, mock_mode: bool = False):
        """Initialize the solver node
        
        Args:
            test_mode: If True, run in test mode (no blockchain interactions)
            mock_mode: If True, use mock services for everything
        """
        self.test_mode = test_mode
        self.mock_mode = mock_mode
        
        logger.info(f"Initializing SolverNode (test={test_mode}, mock={mock_mode})")
        
        # Initialize components based on mode
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components based on the current mode"""
        try:
            # Always initialize data solver
            self.data_solver = DataSolver()
            
            if not self.test_mode and not self.mock_mode:
                # Production mode - components are modules with functions
                self.ipfs_uploader = ipfsUploader
                self.nft_authorizer = nftAuthorizer
                self.solution_submitter = submitSolution
                self.rfd_listener = rfdListener
            else:
                # Test/Mock mode - minimal initialization
                self.ipfs_uploader = None
                self.nft_authorizer = None
                self.solution_submitter = None
                self.rfd_listener = None
                
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _run_production_mode(self):
        """Run the solver node in production mode"""
        logger.info("Starting production mode...")
        
        if not self.rfd_listener:
            logger.error("RFD listener not initialized for production mode")
            return
        
        try:
            # Start listening for RFDs (assuming it has a start_listening function)
            if hasattr(self.rfd_listener, 'start_listening'):
                self.rfd_listener.start_listening(self._process_rfd)
            else:
                logger.error("RFD listener doesn't have start_listening method")
        except Exception as e:
            logger.error(f"Production mode failed: {e}")
    
    def _run_test_mode(self, rfd_file: str = "sample_rfd.json"):
        """Run the solver node in test mode"""
        logger.info(f"Starting test mode with RFD file: {rfd_file}")
        
        try:
            # Load sample RFD
            if not os.path.exists(rfd_file):
                logger.error(f"RFD file not found: {rfd_file}")
                return
            
            with open(rfd_file, 'r') as f:
                rfd = json.load(f)
            
            logger.info(f"Loaded RFD: {rfd.get('name', 'Unknown')}")
            
            # Process the RFD
            result = self._process_rfd(rfd)
            
            if result:
                logger.info("Test mode completed successfully")
            else:
                logger.error("Test mode failed")
                
        except Exception as e:
            logger.error(f"Test mode failed: {e}")
    
    def _process_rfd(self, rfd: Dict[str, Any]) -> bool:
        """Process a single RFD
        
        Args:
            rfd: The RFD to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rfd_id = rfd.get('rfd_id', 'unknown')
            logger.info(f"Processing RFD: {rfd_id}")
            
            # Step 1: Generate dataset
            logger.info("Generating dataset...")
            output_file = self.data_solver.solve(rfd)
            
            if not output_file:
                logger.error("Failed to generate dataset")
                return False
            
            logger.info(f"Dataset saved to: {output_file}")
            
            # Step 2: Upload to IPFS (skip in test/mock mode)
            if not self.test_mode and not self.mock_mode:
                if not self.ipfs_uploader:
                    logger.error("IPFS uploader not available")
                    return False
                
                logger.info("Uploading to IPFS...")
                ipfs_uri = self.ipfs_uploader.upload_to_ipfs(output_file)
                
                if not ipfs_uri:
                    logger.error("Failed to upload to IPFS")
                    return False
                
                logger.info(f"Uploaded to IPFS: {ipfs_uri}")
                
                # Step 3: Verify NFT ownership
                logger.info("Verifying NFT ownership...")
                if not self.nft_authorizer.verify_nft_ownership():
                    logger.error("NFT ownership verification failed")
                    return False
                
                # Step 4: Submit solution
                logger.info("Submitting solution...")
                tx_hash = self.solution_submitter.submit_solution(rfd_id, ipfs_uri)
                
                if tx_hash:
                    logger.info(f"Solution submitted successfully: {tx_hash}")
                else:
                    logger.error("Failed to submit solution")
                    return False
            else:
                logger.info("Skipping IPFS upload and blockchain submission (test/mock mode)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process RFD: {e}")
            return False

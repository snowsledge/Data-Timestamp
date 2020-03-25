"""This singleton class handles merkle tree interactions, maintains a single checksum store and handles outputting proofs in the respective format. It may form the basis for a Zilliqa implementation of the [SideTree](https://github.com/decentralized-identity/sidetree/blob/master/docs/protocol.md) protocol as it is upgraded in the future."""

import calendar
import time

from pymerkle import MerkleTree
from fastapi.encoders import jsonable_encoder
from loguru import logger

from .errors import *


class Tree:
    """Tree class wraps and uses the defaults for pymerkle. It accepts SHA-256 hashes, and UTF-8 encoding. For testing you might benefit from turning off preimage protection"""

    def __init__(self, file=None):
        """sets up the underlying merkle tree
        
        Parameters:
        file (str): Optional recovery of tree state dumped by export().
        """
        if file is None:
            self.merkle = MerkleTree(b"hello world",
                                     b"Hello world", 
                                     b"hello World",
                                     b"Hello World",
                                     b"hello world!",
                                     b"Hello World!", #include  enough hello worlds to construct a path
                                     raw_bytes=False) 
                                     
        else:
            self.merkle = MerkleTree.loadFromFile(file)


    def export(self):
        """export the tree as json to a file called tree_<calendar>.json"""
        filestring = "tree_" + str(calendar.timegm(time.gmtime())) + ".json"
        logger.debug("exporting tree to " + filestring)
        self.merkle.export(filestring)

    @logger.catch
    def stamp(self, checksum):
        """this method will add the checksum to the merkle tree and return the full proof serialized.
        Errors: 
        ChecksumFormatError, ChecksumExistsError"""

        try:
            self.merkle.find_index(checksum)
            raise ChecksumExistsError
        except:
            self.merkle.encryptRecord(checksum)
            logger.info("Checksum: {} added to the tree", checksum)
            return True

        return False

    @logger.catch
    def proofFor(self, checksum):
        """this method will not add a new checksum, but will check it exists and return the proof.
        Errors: 
        ChecksumFormatError, ChecksumNotFoundError"""


        return self.merkle.merkleProof({"checksum": checksum}).serialize()

    def validate(self, proof):
        """this method will return whether or not the proof submitted is valid. Assumes proof was generated by this service, with pymerkle.toJSONString(). Note the proof could be considered valid even if it's checksum isn't in this service's merkle tree.

        Returns: 
        

        Errors: 
        ValidationError"""

        try:
            tmp = Proof.deserialize(proof)
            logger.info("The proof to validate: {}",tmp)
            return self.merkle.validateProof(tmp, get_receipt=True).serialize()
        except:
            raise ValidationError

    def current_root(self):
        return self.merkle.get_commitment()

    def consistency_proof(self, subhash):
        """Returns a consistency proof that the subhash is a valid ancestor root of the current one
        Returns:
        A pymerkle.Proof object serialized to JSON
        """
        return self.merkle.merkleProof({"subhash": subhash}).serialize()
